#!/usr/bin/env python3
"""Run the frozen CP-R3 lexical replication fixtures."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from polybrains import MemoryRecord

from measure_r2_retrieval import POLICIES, evaluate_fixture


CONFIG = Path("configs/retrieval/v02-replication.json")
CLASSES = (
    "answerable-exact", "answerable-paraphrase", "unanswerable-lexical-collision",
    "corrected-stale", "contradictory", "unmatched",
)


def fixture(seed: int, config: dict[str, object]) -> tuple[list[MemoryRecord], list[dict[str, object]]]:
    common = config["common"]
    queries = config["fixtures"][str(seed)]
    now = datetime(2026, 8, 25, 12, tzinfo=timezone.utc) + timedelta(minutes=seed)

    def record(record_id: str, payload: str, confidence: float, source: str, **changes: object) -> MemoryRecord:
        values = {
            "record_id": f"s{seed}-{record_id}", "owner": "a", "frame": "map-a",
            "source": source, "event_time": now, "write_time": now,
            "confidence": confidence, "payload": payload.encode(),
        }
        values.update(changes)
        return MemoryRecord(**values)

    records = [
        record("exact", common["exact_payload"], 0.7, "observation"),
        record("paraphrase", common["paraphrase_payload"], 0.7, "observation"),
        record("collision", common["collision_payload"], 0.99, "high-confidence-distractor"),
        record("stale", common["stale_payload"], 0.9, "observation", event_time=now - timedelta(days=1)),
        record(
            "corrected", common["corrected_payload"], 0.7, "correction",
            supersedes=(f"s{seed}-stale",), reason="new observation",
        ),
        record("contradiction-prior", common["contradictory_prior_payload"], 0.99, "correlated-prior"),
        record("contradiction-outcome", common["contradictory_outcome_payload"], 0.6, "observed-outcome"),
        record("foreign", "harbor gate status closed", 0.99, "foreign-frame", owner="b", frame="map-b"),
    ]
    query_records = [
        ("exact", "answerable-exact", "exact_query", f"s{seed}-exact", "a", "map-a"),
        ("paraphrase", "answerable-paraphrase", "paraphrase_query", f"s{seed}-paraphrase", "a", "map-a"),
        ("collision", "unanswerable-lexical-collision", "collision_query", None, "a", "map-a"),
        ("corrected", "corrected-stale", "corrected_query", f"s{seed}-corrected", "a", "map-a"),
        ("contradiction", "contradictory", "contradictory_query", f"s{seed}-contradiction-outcome", "a", "map-a"),
        ("unmatched", "unmatched", "unmatched_query", None, "b", "map-b"),
    ]
    return records, [
        {
            "query_id": f"s{seed}-{name}", "class": class_name, "text": queries[text_key],
            "expected_record_id": expected, "requester": owner, "frame": frame,
        }
        for name, class_name, text_key, expected, owner, frame in query_records
    ]


def swapped(
    records: list[MemoryRecord], queries: list[dict[str, object]], mapping: dict[str, str]
) -> tuple[list[MemoryRecord], list[dict[str, object]]]:
    swapped_records = [
        MemoryRecord(**{
            **record.__dict__, "owner": mapping[record.owner], "frame": mapping[record.frame],
        })
        for record in records
    ]
    swapped_queries = [
        {**query, "requester": mapping[query["requester"]], "frame": mapping[query["frame"]]}
        for query in queries
    ]
    return swapped_records, swapped_queries


def outcome_signature(result: dict[str, object]) -> dict[str, tuple[object, object, object]]:
    return {
        class_name: (
            details["expected_record_id"], details["record_id"], details["abstention_reason"],
        )
        for class_name, details in result["classes"].items()
    }


def main() -> None:
    config = json.loads(CONFIG.read_text())
    policies = [policy for policy in POLICIES if policy[0] in config["arms"]]
    runs = []
    for seed in config["seeds"]:
        records, queries = fixture(seed, config)
        swapped_records, swapped_queries = swapped(records, queries, config["owner_frame_swap"])
        for policy in policies:
            result = evaluate_fixture(f"seed-{seed}", records, queries, policy)
            swap_result = evaluate_fixture(f"seed-{seed}-swapped", swapped_records, swapped_queries, policy)
            assert outcome_signature(result) == outcome_signature(swap_result)
            result["owner_frame_swap_match"] = True
            runs.append(result)
    assert {tuple(result["classes"]) for result in runs} == {CLASSES}
    assert {
        (result["split"], result["policy"]): (
            result["outcomes"]["correct_retrieval"], result["outcomes"]["false_retrieval"]
        )
        for result in runs
    } == {
        ("seed-11", "v0.1"): (2, 1), ("seed-11", "minimum-3/4"): (2, 0),
        ("seed-23", "v0.1"): (2, 1), ("seed-23", "minimum-3/4"): (1, 0),
        ("seed-37", "v0.1"): (2, 1), ("seed-37", "minimum-3/4"): (2, 1),
    }
    print(json.dumps({"config": str(CONFIG), "runs": runs}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
