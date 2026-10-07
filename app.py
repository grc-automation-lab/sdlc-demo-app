"""
SDLC Demo App — Task Tracker API
----------------------------------
Deliberately tiny. This app has no real business purpose — it exists purely
as a vehicle to generate realistic commit/PR/CI history so that the
sdlc-controls-automation project has something real to evaluate.

Endpoints:
  GET    /tasks            -> list all tasks
  POST   /tasks             -> create a task {"title": "..."}
  GET    /tasks/<id>       -> get one task
  PATCH  /tasks/<id>       -> update a task (e.g. {"completed": true})
  DELETE /tasks/<id>       -> delete a task
  GET    /health            -> liveness check
"""

from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# In-memory store. No database on purpose — keeps the demo dependency-light.
_tasks = {}
_next_id = 1


def _serialize(task_id):
    task = _tasks[task_id]
    return {"id": task_id, "title": task["title"], "completed": task["completed"]}


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.get("/tasks")
def list_tasks():
    return jsonify([_serialize(tid) for tid in _tasks]), 200


@app.post("/tasks")
def create_task():
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    if not title or not isinstance(title, str):
        abort(400, description="title is required and must be a string")

    global _next_id
    task_id = _next_id
    _tasks[task_id] = {"title": title, "completed": False}
    _next_id += 1
    return jsonify(_serialize(task_id)), 201


@app.get("/tasks/<int:task_id>")
def get_task(task_id):
    if task_id not in _tasks:
        abort(404, description="task not found")
    return jsonify(_serialize(task_id)), 200


@app.patch("/tasks/<int:task_id>")
def update_task(task_id):
    if task_id not in _tasks:
        abort(404, description="task not found")

    data = request.get_json(silent=True) or {}
    if "title" in data:
        if not isinstance(data["title"], str) or not data["title"]:
            abort(400, description="title must be a non-empty string")
        _tasks[task_id]["title"] = data["title"]
    if data.get("completed") is not None:
        if not isinstance(data["completed"], bool):
            abort(400, description="completed must be a boolean")
        _tasks[task_id]["completed"] = data["completed"]

    return jsonify(_serialize(task_id)), 200


@app.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    if task_id not in _tasks:
        abort(404, description="task not found")
    del _tasks[task_id]
    return "", 204


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)


   # validation helper placeholder for demo purposes
  # test to validate only codeowner approval
  # this is for testing purpose test01
