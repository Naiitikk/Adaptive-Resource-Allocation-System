# Adaptive Resource Allocation in Multiprogramming Systems

A runnable educational simulator that dynamically distributes CPU and memory among competing programs. The dashboard shows live utilization, workload demand, priority, allocation, throttling status, and the last 30 allocation cycles.

## Project overview

**Goal:** prevent resource bottlenecks while keeping utilization high and ensuring priority-aware fairness. The simulator models changing workloads and rebalances every second.

**Expected outcomes:** a working real-time dashboard, an explainable allocation algorithm, add/remove workload controls, utilization history, and automated tests for capacity and fairness.

**Scope:** this project is a safe user-space simulation. It does not change the operating system scheduler or kill processes. A production version could replace the simulator inputs with `psutil`/cgroup metrics and apply OS-specific limits with appropriate privileges.

## Three modules

1. **Adaptive allocation engine (`allocator.py`)** — models processes, changing demand, priority weights, capacity limits, and reallocation. For example, a high-priority process receives a larger CPU share when total demand exceeds capacity.
2. **Monitoring and visualization (`templates/`, `static/app.js`)** — polls the API, renders utilization meters, a 30-cycle trend chart, and an allocation table. It marks a process as throttled when its allocation is below 70% of demand.
3. **Control/API layer (`app.py`)** — exposes state, pause/resume, reset, add, and remove endpoints and serves the dashboard. It serializes updates with a lock so the simulation thread and HTTP requests cannot race.

## Technology recommendations

- Python 3.10+ and Flask for a small, readable web API.
- Dataclasses and standard-library threading for the baseline simulator.
- HTML/CSS/JavaScript and Canvas for a dependency-free dashboard.
- `pytest` for automated tests; `psutil` is included as the natural extension point for real host metrics.
- For production: FastAPI/WebSockets, Prometheus/Grafana, cgroups or Kubernetes resource quotas, and PostgreSQL/TimescaleDB for long-term telemetry.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. Run tests with `pytest`.

## Implementation plan and efficiency tips

1. Define measurable capacity and fairness constraints.
2. Build the process model and allocator before adding UI.
3. Reallocate from current demand and priority, not hard-coded process names.
4. Keep a bounded history to avoid unbounded memory growth.
5. Protect shared state with a lock and validate all API input.
6. Test capacity, priority fairness, add/remove behavior, and pause/resume.
7. For a real deployment, collect host metrics with `psutil`, apply cgroup quotas, add authentication, and use WebSockets instead of one-second polling.
