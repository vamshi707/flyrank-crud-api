import sqlite3
from fastapi import FastAPI, HTTPException, Response


app = FastAPI()

DB_NAME = "tasks.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Practice Python", 0),
                ("Build AI project", 0),
                ("Learn FastAPI", 1)
            ]
        )

    conn.commit()
    conn.close()


init_db()


tasks = [
    {"id": 1, "title": "Practice Python", "done": False},
    {"id": 2, "title": "Build AI project", "done": False},
    {"id": 3, "title": "Learn FastAPI", "done": True},
]


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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()

    conn.close()

    return [
        {"id": row[0], "title": row[1], "done": bool(row[2])}
        for row in rows
    ]

@app.get("/tasks/{task_id}")

def get_task(task_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()

    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    return {
        "id": row[0],
        "title": row[1],
        "done": bool(row[2])
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

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (title.strip(), 0)
    )

    new_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "id": new_id,
        "title": title.strip(),
        "done": False
    }

@app.put("/tasks/{task_id}")
def update_task(task_id: int, body: dict | None = None):
    if not body:
        raise HTTPException(
            status_code=400,
            detail="Request body cannot be empty"
        )

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if "title" in body:
        if not isinstance(body["title"], str) or not body["title"].strip():
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Title cannot be empty"
            )

    if "done" in body:
        if not isinstance(body["done"], bool):
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Done must be true or false"
            )

    if "title" not in body and "done" not in body:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Provide title or done"
        )

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )

    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    if "title" in body and "done" in body:
        cursor.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (body["title"].strip(), int(body["done"]), task_id)
        )
    elif "title" in body:
        cursor.execute(
            "UPDATE tasks SET title = ? WHERE id = ?",
            (body["title"].strip(), task_id)
        )
    else:
        cursor.execute(
            "UPDATE tasks SET done = ? WHERE id = ?",
            (int(body["done"]), task_id)
        )

    conn.commit()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )

    row = cursor.fetchone()
    conn.close()

    return {
        "id": row[0],
        "title": row[1],
        "done": bool(row[2])
    }


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    conn.commit()
    conn.close()

    return Response(status_code=204)