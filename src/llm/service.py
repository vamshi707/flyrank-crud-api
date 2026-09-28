import json
import os
import time
from pathlib import Path

from fastapi import HTTPException

from src.llm.llm_client import classify_message, get_model_text
from src.llm.schema import TriageOutput


QUARANTINE_PATH = Path("logs/quarantine.jsonl")
COST_PATH = Path("logs/cost.jsonl")


def parse_triage_response(response_text: str) -> TriageOutput:
    data = json.loads(response_text)
    return TriageOutput.model_validate(data)


def write_quarantine(text: str, model_response: str, error: str):
    QUARANTINE_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "input": text,
        "model_response": model_response,
        "error": error,
    }

    with QUARANTINE_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


def write_cost_log(response, duration: float, repair: bool):
    COST_PATH.parent.mkdir(parents=True, exist_ok=True)

    usage = getattr(response, "usage", None)

    record = {
        "prompt_version": "support-triage-v1",
        "model": os.getenv("LLM_MODEL", "unknown"),
        "input_tokens": getattr(usage, "prompt_tokens", 0),
        "output_tokens": getattr(usage, "completion_tokens", 0),
        "duration_seconds": round(duration, 3),
        "repair": repair,
    }

    with COST_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


def classify_with_repair(text: str) -> TriageOutput:
    start = time.perf_counter()

    response = classify_message(text)
    response_text = get_model_text(response)

    try:
        result = parse_triage_response(response_text)

        write_cost_log(
            response,
            time.perf_counter() - start,
            repair=False,
        )

        return result

    except Exception as first_error:
        repair_instruction = """
Return ONLY valid JSON matching the support triage schema.

Required JSON:
{
  "category": "billing|bug|feature|other",
  "urgency": "low|normal|high",
  "confidence": 0.0-1.0,
  "reason": "one short sentence"
}

Do not use markdown.
Do not add explanations.
"""

        repair_response = classify_message(
            f"{repair_instruction}\n\nCustomer message:\n{text}"
        )

        repair_text = get_model_text(repair_response)

        try:
            result = parse_triage_response(repair_text)

            write_cost_log(
                repair_response,
                time.perf_counter() - start,
                repair=True,
            )

            return result

        except Exception as second_error:
            write_quarantine(
                text=text,
                model_response=repair_text,
                error=f"First error: {first_error}; Second error: {second_error}",
            )

            raise HTTPException(
                status_code=422,
                detail="LLM returned invalid structured output.",
            )