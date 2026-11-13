from __future__ import annotations

import threading
import time
from typing import Any

from flask import Flask, jsonify, render_template, request

from allocator import AdaptiveAllocator, ProcessSpec

app = Flask(__name__)
allocator = AdaptiveAllocator()
lock = threading.Lock()


def snapshot() -> dict[str, Any]:
    with lock:
        return allocator.snapshot()


def simulation_loop() -> None:
    while True:
        time.sleep(1)
        with lock:
            allocator.tick()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/state")
def state():
    return jsonify(snapshot())


@app.post("/api/simulation/toggle")
def toggle_simulation():
    with lock:
        allocator.running = not allocator.running
        return jsonify(allocator.snapshot())


@app.post("/api/processes")
def add_process():
    payload = request.get_json(silent=True) or {}
    try:
        process = ProcessSpec.from_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    with lock:
        allocator.add_process(process)
        return jsonify(allocator.snapshot()), 201


@app.delete("/api/processes/<process_id>")
def remove_process(process_id: str):
    with lock:
        if not allocator.remove_process(process_id):
            return jsonify({"error": "Process not found"}), 404
        return jsonify(allocator.snapshot())


@app.post("/api/simulation/reset")
def reset():
    with lock:
        allocator.reset()
        return jsonify(allocator.snapshot())


if __name__ == "__main__":
    threading.Thread(target=simulation_loop, daemon=True).start()
    app.run(debug=False, threaded=True)
