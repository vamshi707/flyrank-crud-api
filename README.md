FLYRANK CRUD API

A simple Task CRUD API built with Python and FastAPI as part of the FlyRank AI Backend Engineering Internship.

FEATURES

- Create tasks
- Read all tasks
- Read a single task
- Update tasks
- Delete tasks
- Input validation
- JSON error responses
- Swagger UI for API testing
- SQLite database storage
- Data persists after server restart

TECH STACK

- Python 3.10+
- FastAPI
- Uvicorn
- SQLite

WHY SQLITE

SQLite is used to replace the in-memory task list from A1 with persistent database storage.
The API endpoints remain the same, but task data is now stored in a SQLite database.

RUN THE PROJECT

Install FastAPI:

pip install "fastapi[standard]"

Start the server:

fastapi dev main.py

The API will be available at:

http://127.0.0.1:8000

Swagger UI:

http://127.0.0.1:8000/docs

DATABASE

Database file:

tasks.db

The tasks.db file and tasks table are created automatically when the application starts.
The database file is gitignored so each clean clone can create its own database.

API ENDPOINTS

GET / - API information
GET /health - Health check
GET /tasks - Get all tasks
GET /tasks/{id} - Get one task
POST /tasks - Create a task
PUT /tasks/{id} - Update a task
DELETE /tasks/{id} - Delete a task

HTTP/1.1 200 OK
date: Tue, 15 Sep 2026 15:35:02 GMT
server: uvicorn
content-length: 143
content-type: application/json

[{"id":1,"title":"Practice Python","done":false},{"id":2,"title":"Build AI project","done":false},{"id":3,"title":"Learn FastAPI","done":true}]

SWAGGER UI SCREENSHOT

Swagger screenshot: image.png

DATABASE EXPLORATION

Example SQL query:

SELECT * FROM tasks;

SQLite database was explored and modified using DB Browser for SQLite, and the FastAPI API correctly reflected the database changes.

DATABASE SCREENSHOT

Database screenshot: db-image copy.png

DOCKER SETUP

This project runs the FastAPI application and PostgreSQL database using Docker Compose.

RUN WITH DOCKER COMPOSE

1. Copy the example environment file:

cp .env.example .env

2. Start the complete stack:

docker compose up

The API will be available at:

http://127.0.0.1:8000

Swagger UI:

http://127.0.0.1:8000/docs


ENVIRONMENT VARIABLES

DATABASE_URL=postgres://postgres:dev@db:5432/tasks

The .env file contains the database connection string and is ignored by Git.
The .env.example file is committed to the repository as a template.


DATABASE

PostgreSQL is used as the persistent database.

The PostgreSQL database runs inside Docker.
A Docker volume named taskdata stores the database data.

The data remains available after:

docker compose down

docker compose up


DOCKER COMPOSE

The complete application stack can be started with one command:

docker compose up


API ENDPOINTS

GET / - API information
GET /health - Health check
GET /tasks - Get all tasks
GET /tasks/{id} - Get one task
POST /tasks - Create a task
PUT /tasks/{id} - Update a task
DELETE /tasks/{id} - Delete a task


DOCKER TEST

Example:

curl -i http://127.0.0.1:8000/tasks

The API returns the tasks stored in PostgreSQL.