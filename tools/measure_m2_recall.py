#!/usr/bin/env python3
"""Reproduce and falsify the frozen v0.1 private-retrieval baseline."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import median
from time import perf_counter_ns

from polybrains import EpisodicStore, MemoryRecord, retrieve_claim


NOW = datetime(2026, 8, 25, tzinfo=timezone.utc)


@dataclass(frozen=True)
class GroundTruthQuery:
    query_id: str
    owner: str
    frame: str
    text: str
    expected_record_id: str | None


def episode(record_id: str, owner: str, frame: str, text: str, confidence: float) -> MemoryRecord:
    return MemoryRecord(record_id, owner, frame, "m2-recall", NOW, NOW, confidence, text.encode())


def build_store(owner: str, frame: str, targets: int = 100, noise: int = 20, missing: str | None = None) -> EpisodicStore:
    store = EpisodicStore(owner, frame)
    for index in range(targets):
        record_id = f"{owner}-target-{index}"
        if record_id != missing:
            store.append(episode(record_id, owner, frame, f"cue_{owner}_{index} fact_{index}", 0.5))
    for index in range(noise):
        store.append(episode(f"{owner}-noise-{index}", owner, frame, f"noise_{owner}_{index}", 0.99))
    return store


def queries(stores: tuple[EpisodicStore, ...]) -> tuple[GroundTruthQuery, ...]:
    answerable = tuple(
        GroundTruthQuery(
            f"answerable-{store.owner}-{index}", store.owner, store.frame,
            f"cue_{store.owner}_{index}", f"{store.owner}-target-{index}",
        )
        for store in stores for index in range(100)
    )
    unanswerable = tuple(
        GroundTruthQuery(
            f"unanswerable-{store.owner}-{index}", store.owner, store.frame,
            f"noise_{store.owner}_{index}", None,
        )
        for store in stores for index in range(20)
    )
    return answerable + unanswerable


def outcomes(expected: list[str | None], returned: list[str | None]) -> dict[str, int]:
    counts = {
        "correct_retrieval": 0, "wrong_retrieval": 0, "false_retrieval": 0,
        "correct_abstention": 0, "missed_answer": 0,
    }
    for truth, result in zip(expected, returned, strict=True):
        if truth is None:
            counts["correct_abstention" if result is None else "false_retrieval"] += 1
        elif result is None:
            counts["missed_answer"] += 1
        elif result == truth:
            counts["correct_retrieval"] += 1
        else:
            counts["wrong_retrieval"] += 1
    return counts


def complete_provenance(raw: bytes) -> bool:
    try:
        record = MemoryRecord.from_bytes(raw)
    except (KeyError, TypeError, ValueError):
        return False
    return bool(
        record.record_id and record.owner and record.frame and record.source
        and record.event_time.tzinfo and record.write_time.tzinfo
        and 0.0 <= record.confidence <= 1.0 and record.lifecycle
        and len(record.content_hash) == 64 and record.to_bytes() == raw
    )


def latency_ms(store: EpisodicStore, added_ns: int = 0) -> tuple[float, float]:
    samples = []
    for _ in range(5):
        for index in range(100):
            start = perf_counter_ns()
            store.retrieve(store.owner, store.frame, f"cue_{store.owner}_{index}")
            samples.append((perf_counter_ns() - start + added_ns) / 1_000_000)
    samples.sort()
    return median(samples), samples[int(len(samples) * 0.95) - 1]


def deterministic_result() -> dict[str, object]:
    stores = (build_store("a", "map-a"), build_store("b", "map-b"))
    ground_truth = queries(stores)
    stores_by_owner = {store.owner: store for store in stores}
    returned_records = [
        stores_by_owner[query.owner].retrieve(query.owner, query.frame, query.text)
        for query in ground_truth
    ]
    expected = [query.expected_record_id for query in ground_truth]
    returned = [record.record_id if record else None for record in returned_records]

    missing = (build_store("a", "map-a", missing="a-target-0"), stores[1])
    missing_by_owner = {store.owner: store for store in missing}
    removal_returned = []
    for query in ground_truth[:200]:
        record = missing_by_owner[query.owner].retrieve(query.owner, query.frame, query.text)
        removal_returned.append(record.record_id if record else None)

    small = stores[0]
    large = build_store("a", "map-a", targets=1000, noise=200)
    result = {
        "fixture": "v01-m2-explicit-ground-truth",
        "policy": "v0.1-lexical-overlap",
        "queries": len(ground_truth),
        "outcomes": outcomes(expected, returned),
        "provenance": {
            "complete": sum(complete_provenance(record.to_bytes()) for record in returned_records if record),
            "returned": sum(record is not None for record in returned_records),
        },
        "removal_control": outcomes(expected[:200], removal_returned),
        "scale_control": {
            "small_records": len(small.records), "large_records": len(large.records),
            "small_examined": retrieve_claim(small.records, "cue_a_0", "a", "map-a").examined,
            "large_examined": retrieve_claim(large.records, "cue_a_0", "a", "map-a").examined,
        },
        "storage": {
            "small_payload_bytes": small.payload_bytes, "large_payload_bytes": large.payload_bytes,
            "small_serialized_bytes": sum(len(record.to_bytes()) for record in small.records),
            "large_serialized_bytes": sum(len(record.to_bytes()) for record in large.records),
        },
    }
    verify_controls(result, expected, returned, returned_records, small)
    return result


def verify_controls(
    result: dict[str, object], expected: list[str | None], returned: list[str | None],
    returned_records: list[MemoryRecord | None], small: EpisodicStore,
) -> None:
    assert result["outcomes"] == {
        "correct_retrieval": 200, "wrong_retrieval": 0, "false_retrieval": 40,
        "correct_abstention": 0, "missed_answer": 0,
    }
    assert result["provenance"] == {"complete": 240, "returned": 240}
    assert result["removal_control"]["correct_retrieval"] == 199
    assert result["removal_control"]["missed_answer"] == 1
    assert result["scale_control"] == {
        "small_records": 120, "large_records": 1200,
        "small_examined": 120, "large_examined": 1200,
    }

    wrong_expected = expected.copy()
    wrong_expected[0] = "a-target-1"
    assert outcomes(wrong_expected, returned)["wrong_retrieval"] == 1
    abstained = returned.copy()
    abstained[200] = None
    abstention_scores = outcomes(expected, abstained)
    assert abstention_scores["false_retrieval"] == 39
    assert abstention_scores["correct_abstention"] == 1
    first_raw = returned_records[0].to_bytes()
    corrupted = first_raw.replace(returned_records[0].content_hash.encode(), b"0" * 64)
    assert not complete_provenance(corrupted)
    expanded = (*small.records, episode("a-extra", "a", "map-a", "irrelevant", 0.5))
    assert retrieve_claim(expanded, "cue_a_0", "a", "map-a").examined == 121
    assert sum(len(record.payload) for record in expanded) > result["storage"]["small_payload_bytes"]
    assert sum(len(record.to_bytes()) for record in expanded) > result["storage"]["small_serialized_bytes"]
    assert latency_ms(small, added_ns=10_000_000)[0] > latency_ms(small)[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    args = parser.parse_args()
    result = deterministic_result()
    if args.json:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return

    small_latency = latency_ms(build_store("a", "map-a"))
    large_latency = latency_ms(build_store("a", "map-a", targets=1000, noise=200))
    print("private recall@1: 200/200 (100.0%)")
    print("removal control: 199/200 (99.5%)")
    print("false retrieval: 40/40 (100.0%)")
    print("provenance completeness: 240/240 (100.0%)")
    print("examined/query: 120 -> 1200 (10.0x)")
    print(
        f"latency median/p95 ms: {small_latency[0]:.3f}/{small_latency[1]:.3f} -> "
        f"{large_latency[0]:.3f}/{large_latency[1]:.3f}"
    )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
