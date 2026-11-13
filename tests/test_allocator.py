from allocator import AdaptiveAllocator, ProcessSpec


def test_allocation_respects_capacity():
    allocator = AdaptiveAllocator()
    state = allocator.snapshot()
    assert state["system"]["cpu_used"] <= 100
    assert state["system"]["memory_used"] <= 8192


def test_high_priority_process_receives_fair_share():
    allocator = AdaptiveAllocator()
    allocator.processes = [
        ProcessSpec("Low", 1, 100, 1000, "low"),
        ProcessSpec("High", 10, 100, 1000, "high"),
    ]
    allocator._allocate()
    assert allocator.processes[1].cpu_allocation > allocator.processes[0].cpu_allocation


def test_add_and_remove_process():
    allocator = AdaptiveAllocator()
    count = len(allocator.processes)
    allocator.add_process(ProcessSpec("Test", 5, 20, 200, "test"))
    assert len(allocator.processes) == count + 1
    assert allocator.remove_process("test")
    assert len(allocator.processes) == count
