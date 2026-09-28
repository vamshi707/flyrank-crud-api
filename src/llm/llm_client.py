import os
import random
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PROMPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "prompts"
    / "support-triage-v1.md"
)


def load_system_prompt():
    return PROMPT_PATH.read_text(encoding="utf-8")


def get_llm_client():
    return OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        timeout=30.0,
        max_retries=0,
    )


def classify_message(text: str):
    client = get_llm_client()

    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            return client.chat.completions.create(
                model=os.environ["LLM_MODEL"],
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": load_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": text,
                    },
                ],
            )

        except Exception as error:
            error_text = str(error).lower()

            retryable = (
                "timeout" in error_text
                or "429" in error_text
                or "500" in error_text
                or "502" in error_text
                or "503" in error_text
                or "504" in error_text
            )

            if not retryable or attempt == max_attempts - 1:
                raise

            delay = (2 ** attempt) + random.uniform(0, 0.5)
            time.sleep(delay)


def get_model_text(response):
    text = response.choices[0].message.content.strip()

    print("\n--- MODEL RESPONSE ---")
    print(text)
    print("--- END MODEL RESPONSE ---\n")

    return text