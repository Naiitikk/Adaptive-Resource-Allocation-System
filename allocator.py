from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProcessSpec:
    name: str
    priority: int = 5
    cpu_demand: float = 50.0
    memory_demand: float = 256.0
    process_id: str = ""
    cpu_allocation: float = 0.0
    memory_allocation: float = 0.0
    status: str = "Running"
    cpu_history: list[float] = field(default_factory=list)
    memory_history: list[float] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ProcessSpec":
        name = str(payload.get("name", "")).strip()
        if not name or len(name) > 40:
            raise ValueError("A process name between 1 and 40 characters is required.")
        try:
            priority = int(payload.get("priority", 5))
            cpu_demand = float(payload.get("cpu_demand", 50))
            memory_demand = float(payload.get("memory_demand", 256))
        except (TypeError, ValueError) as exc:
            raise ValueError("Priority, CPU demand, and memory demand must be numeric.") from exc
        if not 1 <= priority <= 10:
            raise ValueError("Priority must be between 1 and 10.")
        if not 1 <= cpu_demand <= 100 or not 1 <= memory_demand <= 4096:
            raise ValueError("CPU demand must be 1-100 and memory demand must be 1-4096 MB.")
        process_id = f"p-{int(time.time() * 1000)}-{random.randint(100, 999)}"
        return cls(name, priority, cpu_demand, memory_demand, process_id)


class AdaptiveAllocator:
    """Weighted fair-share allocator with demand-aware reallocation."""

    def __init__(self) -> None:
        self.running = True
        self.tick_count = 0
        self.processes: list[ProcessSpec] = []
        self.cpu_capacity = 100.0
        self.memory_capacity = 8192.0
        self.cpu_history: list[float] = []
        self.memory_history: list[float] = []
        self.last_action = "System initialized"
        self.reset()

    def reset(self) -> None:
        self.processes = [
            ProcessSpec("Web Server", 8, 78, 1024, "p-web"),
            ProcessSpec("Data Worker", 6, 62, 2048, "p-data"),
            ProcessSpec("Batch Job", 3, 42, 3072, "p-batch"),
            ProcessSpec("Monitoring", 9, 25, 512, "p-monitor"),
        ]
        self.tick_count = 0
        self.cpu_history = []
        self.memory_history = []
        self.last_action = "Simulation reset"
        self._allocate()

    def add_process(self, process: ProcessSpec) -> None:
        self.processes.append(process)
        self._allocate()
        self.last_action = f"Added {process.name}"

    def remove_process(self, process_id: str) -> bool:
        original_count = len(self.processes)
        self.processes = [p for p in self.processes if p.process_id != process_id]
        removed = len(self.processes) != original_count
        if removed:
            self._allocate()
            self.last_action = "Process removed and resources rebalanced"
        return removed

    def tick(self) -> None:
        if not self.running:
            return
        self.tick_count += 1
        for process in self.processes:
            # Demand changes model changing workloads while staying reproducible enough for a demo.
            process.cpu_demand = max(5.0, min(100.0, process.cpu_demand + random.uniform(-7, 7)))
            process.memory_demand = max(128.0, min(4096.0, process.memory_demand + random.uniform(-160, 160)))
        self._allocate()

    def _allocate(self) -> None:
        if not self.processes:
            return
        weights = [max(1, p.priority) * max(1.0, p.cpu_demand / 25) for p in self.processes]
        total_weight = sum(weights)
        for process, weight in zip(self.processes, weights):
            process.cpu_allocation = min(process.cpu_demand, self.cpu_capacity * weight / total_weight)

        # Memory is weighted by priority and capped by demand, then distributed again if capacity remains.
        memory_weights = [max(1, p.priority) * max(1.0, p.memory_demand / 512) for p in self.processes]
        total_memory_weight = sum(memory_weights)
        for process, weight in zip(self.processes, memory_weights):
            process.memory_allocation = min(process.memory_demand, self.memory_capacity * weight / total_memory_weight)

        for process in self.processes:
            process.status = "Throttled" if process.cpu_allocation < process.cpu_demand * 0.7 else "Running"
            process.cpu_history.append(round(process.cpu_allocation, 2))
            process.memory_history.append(round(process.memory_allocation, 2))
            process.cpu_history = process.cpu_history[-30:]
            process.memory_history = process.memory_history[-30:]

        self.cpu_history.append(round(sum(p.cpu_allocation for p in self.processes), 2))
        self.memory_history.append(round(sum(p.memory_allocation for p in self.processes), 2))
        self.cpu_history = self.cpu_history[-30:]
        self.memory_history = self.memory_history[-30:]
        self.last_action = "Resources rebalanced using demand and priority weights"

    def snapshot(self) -> dict[str, Any]:
        cpu_used = sum(p.cpu_allocation for p in self.processes)
        memory_used = sum(p.memory_allocation for p in self.processes)
        return {
            "running": self.running,
            "tick": self.tick_count,
            "last_action": self.last_action,
            "system": {
                "cpu_used": round(cpu_used, 2),
                "cpu_capacity": self.cpu_capacity,
                "memory_used": round(memory_used, 2),
                "memory_capacity": self.memory_capacity,
                "cpu_percent": round(cpu_used / self.cpu_capacity * 100, 2),
                "memory_percent": round(memory_used / self.memory_capacity * 100, 2),
            },
            "history": {"cpu": self.cpu_history, "memory": self.memory_history},
            "processes": [
                {
                    "id": p.process_id,
                    "name": p.name,
                    "priority": p.priority,
                    "cpu_demand": round(p.cpu_demand, 2),
                    "cpu_allocation": round(p.cpu_allocation, 2),
                    "memory_demand": round(p.memory_demand, 2),
                    "memory_allocation": round(p.memory_allocation, 2),
                    "status": p.status,
                    "cpu_history": p.cpu_history,
                    "memory_history": p.memory_history,
                }
                for p in self.processes
            ],
        }
