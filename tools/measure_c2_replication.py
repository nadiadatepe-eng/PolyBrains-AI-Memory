#!/usr/bin/env python3
"""Run the frozen v0.3 contradiction-reliability replication."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from polybrains import MemoryRecord

from measure_c1_reliability import NOW, POLICIES, evaluate


CONFIG = Path("configs/retrieval/v03-replication.json")


def fixture(seed: int, item: dict[str, object]) -> tuple[list[MemoryRecord], list[dict[str, object]]]:
    prefix = f"s{seed}"
    when = NOW + timedelta(minutes=seed)

    def record(record_id: str, payload: str, confidence: float, **changes: object) -> MemoryRecord:
        values = {
            "record_id": f"{prefix}-{record_id}", "owner": "a", "frame": "map-a",
            "source": "memory", "event_time": when, "write_time": when,
            "confidence": confidence, "payload": payload.encode(),
        }
        values.update(changes)
        return MemoryRecord(**values)

    prior = record("prior", item["prior"], item["prior_confidence"])
    outcome = record("outcome", item["outcome"], item["outcome_confidence"])
    if item["evidence_mode"] == "superseding":
        stale = record("evidence-stale", "old check supports prior", 0.8, supports=(prior.record_id,))
        evidence = record(
            "evidence", item["evidence"], 0.7, supports=(outcome.record_id,),
            contradicts=(prior.record_id,), supersedes=(stale.record_id,), reason="corrected check",
        )
        linked = [stale, evidence]
    else:
        linked = [
            record(
                "evidence", item["evidence"], 0.7, supports=(outcome.record_id,),
                contradicts=(prior.record_id,),
            )
        ]
    ambiguous_a = record("ambiguous-a", item["ambiguous_a"], 0.9)
    ambiguous_b = record("ambiguous-b", item["ambiguous_b"], 0.8)
    exact = record("exact", item["exact"], 0.75)
    missing_a = record("missing-a", f"backup {item['subject']} status ready", 0.85)
    missing_b = record("missing-b", f"reserve {item['subject']} status ready", 0.65)
    foreign = record("foreign", item["prior"], 1.0, owner="b", frame="map-b")
    records = [prior, outcome, *linked, ambiguous_a, ambiguous_b, exact, missing_a, missing_b, foreign]
    ambiguous_query = " ".join(item["ambiguous_a"].split()[1:])
    queries = [
        {
            "query_id": f"{prefix}-verified", "class": "verified-contradiction",
            "text": f"{item['subject']} current status", "requester": "a", "frame": "map-a",
            "candidate_ids": [prior.record_id, outcome.record_id], "expected_record_id": outcome.record_id,
        },
        {
            "query_id": f"{prefix}-unverified", "class": "unverified-contradiction",
            "text": ambiguous_query, "requester": "a", "frame": "map-a",
            "candidate_ids": [ambiguous_a.record_id, ambiguous_b.record_id], "expected_record_id": None,
        },
        {
            "query_id": f"{prefix}-exact", "class": "uncontested-exact",
            "text": item["exact"], "requester": "a", "frame": "map-a",
            "candidate_ids": [exact.record_id], "expected_record_id": exact.record_id,
        },
        {
            "query_id": f"{prefix}-missing", "class": "missing-outcome",
            "text": f"{item['subject']} status ready", "requester": "a", "frame": "map-a",
            "candidate_ids": [missing_a.record_id, missing_b.record_id], "expected_record_id": None,
        },
    ]
    return records, queries


def swapped(
    records: list[MemoryRecord], queries: list[dict[str, object]], mapping: dict[str, str]
) -> tuple[list[MemoryRecord], list[dict[str, object]]]:
    swapped_records = [
        MemoryRecord(**{**record.__dict__, "owner": mapping[record.owner], "frame": mapping[record.frame]})
        for record in records
    ]
    swapped_queries = [
        {**query, "requester": mapping[query["requester"]], "frame": mapping[query["frame"]]}
        for query in queries
    ]
    return swapped_records, swapped_queries


def signature(result: dict[str, object]) -> dict[str, tuple[object, object]]:
    return {
        name: (details["record_id"], details["abstention_reason"])
        for name, details in result["classes"].items()
    }


def main() -> None:
    config = json.loads(CONFIG.read_text())
    runs = []
    for seed in config["seeds"]:
        records, queries = fixture(seed, config["fixtures"][str(seed)])
        swap_records, swap_queries = swapped(records, queries, config["owner_frame_swap"])
        for policy in POLICIES:
            result = evaluate(f"seed-{seed}", records, queries, policy)
            swap_result = evaluate(f"seed-{seed}-swapped", swap_records, swap_queries, policy)
            assert signature(result) == signature(swap_result)
            result["owner_frame_swap_match"] = True
            runs.append(result)
    assert {tuple(result["classes"]) for result in runs} == {tuple(config["required_classes"])}
    by_run = {(result["split"], result["policy"]): result["outcomes"] for result in runs}
    for seed in config["seeds"]:
        candidate = by_run[(f"seed-{seed}", "outcome-provenance")]
        controls = [by_run[(f"seed-{seed}", policy)] for policy in POLICIES[:2]]
        assert candidate == {
            "correct_retrieval": 2, "wrong_retrieval": 0, "false_retrieval": 0,
            "correct_abstention": 2, "missed_answer": 0,
        }
        assert all(candidate["correct_retrieval"] >= control["correct_retrieval"] for control in controls)
        assert all(candidate["wrong_retrieval"] <= control["wrong_retrieval"] for control in controls)
        assert all(candidate["false_retrieval"] < control["false_retrieval"] for control in controls)
    print(json.dumps({"config": str(CONFIG), "runs": runs}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
