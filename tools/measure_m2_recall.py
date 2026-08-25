#!/usr/bin/env python3
"""Measure the pre-registered CP-M2 private-memory baseline."""

from datetime import datetime, timezone
from statistics import median
from time import perf_counter_ns

from polybrains import EpisodicStore, MemoryRecord, retrieve, retrieve_claim


NOW = datetime(2026, 8, 25, tzinfo=timezone.utc)


def episode(record_id: str, owner: str, frame: str, text: str, confidence: float) -> MemoryRecord:
    return MemoryRecord(record_id, owner, frame, "m2-recall", NOW, NOW, confidence, text.encode())


def build_store(
    owner: str,
    frame: str,
    targets: int = 100,
    noise: int = 20,
    missing: str | None = None,
) -> EpisodicStore:
    store = EpisodicStore(owner, frame)
    for index in range(targets):
        record_id = f"{owner}-target-{index}"
        if record_id != missing:
            store.append(episode(record_id, owner, frame, f"cue_{owner}_{index} fact_{index}", 0.5))
    for index in range(noise):
        store.append(episode(f"{owner}-noise-{index}", owner, frame, f"noise_{owner}_{index}", 0.99))
    return store


def recalled(stores: tuple[EpisodicStore, ...]) -> int:
    return sum(
        getattr(store.retrieve(store.owner, store.frame, f"cue_{store.owner}_{index}"), "record_id", None)
        == f"{store.owner}-target-{index}"
        for store in stores
        for index in range(100)
    )


def latency_ms(store: EpisodicStore) -> tuple[float, float]:
    samples = []
    for _ in range(5):
        for index in range(100):
            start = perf_counter_ns()
            store.retrieve(store.owner, store.frame, f"cue_{store.owner}_{index}")
            samples.append((perf_counter_ns() - start) / 1_000_000)
    samples.sort()
    return median(samples), samples[int(len(samples) * 0.95) - 1]


def complete_provenance(record: MemoryRecord) -> bool:
    return bool(
        record.record_id
        and record.owner
        and record.frame
        and record.source
        and record.event_time.tzinfo
        and record.write_time.tzinfo
        and 0.0 <= record.confidence <= 1.0
        and record.lifecycle
        and len(record.content_hash) == 64
        and MemoryRecord.from_bytes(record.to_bytes()) == record
    )


def main() -> None:
    stores = (build_store("a", "map-a"), build_store("b", "map-b"))
    recall = recalled(stores)
    no_memory = sum(
        retrieve((), f"cue_{store.owner}_{index}") is not None
        for store in stores
        for index in range(100)
    )
    removal_control = recalled((build_store("a", "map-a", missing="a-target-0"), stores[1]))
    valid_results = [
        store.retrieve(store.owner, store.frame, f"cue_{store.owner}_{index}")
        for store in stores
        for index in range(100)
    ]
    false_results = [
        store.retrieve(store.owner, store.frame, f"noise_{store.owner}_{index}")
        for store in stores
        for index in range(20)
    ]
    false_retrieval = sum(result is not None for result in false_results)
    no_memory_false = sum(retrieve((), f"noise_{index}") is not None for index in range(40))
    provenance = sum(complete_provenance(record) for record in (*valid_results, *false_results))

    small = stores[0]
    large = build_store("a", "map-a", targets=1000, noise=200)
    small_latency = latency_ms(small)
    large_latency = latency_ms(large)
    small_examined = retrieve_claim(small.records, "cue_a_0", "a", "map-a").examined
    large_examined = retrieve_claim(large.records, "cue_a_0", "a", "map-a").examined
    payload_ratio = large.payload_bytes / small.payload_bytes
    serialized_ratio = sum(len(record.to_bytes()) for record in large.records) / sum(
        len(record.to_bytes()) for record in small.records
    )
    try:
        stores[0].retrieve("b", "map-b", "cue_a_000")
        isolated = False
    except PermissionError:
        isolated = True

    assert (recall, no_memory, removal_control, isolated) == (200, 0, 199, True)
    assert (false_retrieval, no_memory_false, provenance) == (40, 0, 240)
    assert (small_examined, large_examined) == (120, 1200)
    assert 9 <= payload_ratio <= 12 and 9 <= serialized_ratio <= 12
    assert large_latency[0] > small_latency[0]
    print(f"private recall@1: {recall}/200 (100.0%)")
    print(f"no-memory recall@1: {no_memory}/200 (0.0%)")
    print(f"removal control: {removal_control}/200 (99.5%)")
    print("isolation: pass")
    print(f"false retrieval: {false_retrieval}/40 (100.0%); no memory: {no_memory_false}/40")
    print(f"provenance completeness: {provenance}/240 (100.0%)")
    print(f"examined/query: {small_examined} -> {large_examined} ({large_examined / small_examined:.1f}x)")
    print(
        f"latency median/p95 ms: {small_latency[0]:.3f}/{small_latency[1]:.3f} -> "
        f"{large_latency[0]:.3f}/{large_latency[1]:.3f}"
    )
    print(f"storage growth payload/serialized: {payload_ratio:.2f}x/{serialized_ratio:.2f}x")


if __name__ == "__main__":
    main()
