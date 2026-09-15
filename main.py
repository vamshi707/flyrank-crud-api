from fastapi import FastAPI, HTTPException, Response

app = FastAPI()


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
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )


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

    new_id = 1

    while any(task["id"] == new_id for task in tasks):
        new_id += 1

    new_task = {
        "id": new_id,
        "title": title.strip(),
        "done": False
    }

    tasks.append(new_task)

    return new_task


@app.put("/tasks/{task_id}")
def update_task(task_id: int, body: dict | None = None):
    if not body:
        raise HTTPException(
            status_code=400,
            detail="Request body cannot be empty"
        )

    for task in tasks:
        if task["id"] == task_id:

            if "title" in body:
                if not isinstance(body["title"], str) or not body["title"].strip():
                    raise HTTPException(
                        status_code=400,
                        detail="Title cannot be empty"
                    )

                task["title"] = body["title"].strip()

            if "done" in body:
                if not isinstance(body["done"], bool):
                    raise HTTPException(
                        status_code=400,
                        detail="Done must be true or false"
                    )

                task["done"] = body["done"]

            if "title" not in body and "done" not in body:
                raise HTTPException(
                    status_code=400,
                    detail="Provide title or done"
                )

            return task

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(index)
            return Response(status_code=204)

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )