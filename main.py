from fastapi import FastAPI, HTTPException, Response
from db import init_db, get_connection

app = FastAPI()

init_db()


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