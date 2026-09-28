import json
from src.llm.service import classify_with_repair
import os
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request
from src.llm.schema import TriageInput, TriageOutput, Category, Urgency
from fastapi import FastAPI, HTTPException, Response, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from supabase_client import supabase
from db import init_db, get_connection

app = FastAPI()
security = HTTPBearer()


class AuthBody(BaseModel):
    email: str
    password: str




@app.get("/")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/signup", status_code=201)
def signup(body: AuthBody):
    try:
        result = supabase.auth.sign_up({
            "email": body.email,
            "password": body.password
        })

        return {
            "message": "Signup successful",
            "user": result.user
        }

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Signup failed"
        )

@app.post("/auth/login")
def login(body: AuthBody):
    try:
        result = supabase.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password
        })

        return {
            "message": "Login successful",
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token
        }

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

@app.get("/public/info")
def public_info():
    return {
        "message": "This is a public endpoint",
        "status": "ok"
    }

def verify_token(token: str):
    try:
        response = supabase.auth.get_user(token)

        if response.user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return response.user

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    return verify_token(credentials.credentials)


@app.get("/protected/profile")
def protected_profile(user=Depends(get_current_user)):
    return {
        "message": "Protected profile",
        "user": {
            "id": user.id,
            "email": user.email
        }
    }


@app.get("/protected/dashboard")
def protected_dashboard(user=Depends(get_current_user)):
    return {
        "message": "Welcome to protected dashboard",
        "user": {
            "id": user.id,
            "email": user.email
        }
    }


@app.post("/auth/logout", status_code=204)
def logout(user=Depends(get_current_user)):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    return Response(status_code=204)
    
@app.get("/tasks")
def get_tasks():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tasks")
            rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "title": row[1],
            "done": row[2]
        }
        for row in rows
    ]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM tasks WHERE id = %s",
                (task_id,)
            )
            row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2]
    }


@app.post("/tasks", status_code=201)
def create_task(body: dict | None = None):
    if not body or "title" not in body:
        raise HTTPException(
            status_code=400,
            detail="Title is required"
        )

    title = body["title"]

    if not isinstance(title, str) or not title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
                (title.strip(), False)
            )
            row = cursor.fetchone()
        conn.commit()

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2]
    }


@app.put("/tasks/{task_id}")
def update_task(task_id: int, body: dict | None = None):
    if not body:
        raise HTTPException(
            status_code=400,
            detail="Request body cannot be empty"
        )

    if "title" in body:
        if not isinstance(body["title"], str) or not body["title"].strip():
            raise HTTPException(
                status_code=400,
                detail="Title cannot be empty"
            )

    if "done" in body:
        if not isinstance(body["done"], bool):
            raise HTTPException(
                status_code=400,
                detail="Done must be true or false"
            )

    if "title" not in body and "done" not in body:
        raise HTTPException(
            status_code=400,
            detail="Provide title or done"
        )

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute(
                "SELECT * FROM tasks WHERE id = %s",
                (task_id,)
            )

            if cursor.fetchone() is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Task {task_id} not found"
                )

            if "title" in body and "done" in body:
                cursor.execute(
                    """
                    UPDATE tasks
                    SET title = %s, done = %s
                    WHERE id = %s
                    RETURNING *
                    """,
                    (
                        body["title"].strip(),
                        body["done"],
                        task_id
                    )
                )

            elif "title" in body:
                cursor.execute(
                    """
                    UPDATE tasks
                    SET title = %s
                    WHERE id = %s
                    RETURNING *
                    """,
                    (
                        body["title"].strip(),
                        task_id
                    )
                )

            else:
                cursor.execute(
                    """
                    UPDATE tasks
                    SET done = %s
                    WHERE id = %s
                    RETURNING *
                    """,
                    (
                        body["done"],
                        task_id
                    )
                )

            row = cursor.fetchone()

        conn.commit()

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2]
    }


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM tasks WHERE id = %s",
                (task_id,)
            )

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Task {task_id} not found"
                )

        conn.commit()

    return Response(status_code=204)

def parse_triage_response(response_text: str) -> TriageOutput:
    data = json.loads(response_text)
    return TriageOutput.model_validate(data)


@app.post("/triage", response_model=TriageOutput)
def triage(data: TriageInput):

    # Kill switch
    if os.getenv("LLM_ENABLED", "true").lower() == "false":
        return TriageOutput(
            category=Category.other,
            urgency=Urgency.low,
            confidence=0.0,
            reason="LLM is currently disabled."
        )

    # Stub mode
    if os.getenv("LLM_STUB") == "1":
        return TriageOutput(
            category=Category.other,
            urgency=Urgency.normal,
            confidence=0.5,
            reason="Stub response for testing."
        )


    return classify_with_repair(data.text)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    errors = exc.errors()

    field = "unknown"

    if errors:
        location = errors[0].get("loc", [])
        if location:
            field = str(location[-1])

    return JSONResponse(
        status_code=400,
        content={
            "message": f"Invalid field: {field}"
        }
    )