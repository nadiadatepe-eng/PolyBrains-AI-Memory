#!/usr/bin/env python3
"""Evaluate the frozen v0.3 contradiction-reliability fixtures."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from time import perf_counter_ns

from polybrains import MemoryRecord
from polybrains.memory import _active_records

from measure_m2_recall import complete_provenance, outcomes


NOW = datetime(2026, 8, 26, 12, tzinfo=timezone.utc)
POLICIES = ("similarity-only", "confidence-ranked", "outcome-provenance")


def tokens(value: str) -> set[str]:
    return set(re.findall(r"\w+", value.casefold()))


def load_fixture(split: str) -> tuple[list[MemoryRecord], list[dict[str, object]]]:
    fixture = json.loads(Path(f"configs/retrieval/v03-{split}.json").read_text())
    records = [
        MemoryRecord(
            record_id=item["record_id"], owner=item["owner"], frame=item["frame"],
            source=item["source"], event_time=NOW, write_time=NOW,
            confidence=item["confidence"], payload=item["payload"].encode(),
            supports=tuple(item.get("supports", ())),
            contradicts=tuple(item.get("contradicts", ())),
        )
        for item in fixture["records"]
    ]
    return records, fixture["queries"]


def retrieve(records: list[MemoryRecord], query: dict[str, object], policy: str) -> dict[str, object]:
    live = _active_records(
        record for record in records
        if (record.owner, record.frame) == (query["requester"], query["frame"])
    )
    allowed = set(query["candidate_ids"])
    query_tokens = tokens(query["text"])
    candidates = [
        record for record in live
        if record.record_id in allowed and query_tokens & tokens(record.payload.decode())
    ]
    overlap = {record.record_id: len(query_tokens & tokens(record.payload.decode())) for record in candidates}
    reason = None
    evidence: list[str] = []
    if not candidates:
        record = None
        reason = "no-candidate"
    elif policy == "similarity-only":
        record = max(candidates, key=lambda item: (overlap[item.record_id], item.record_id))
    elif policy == "confidence-ranked":
        record = max(candidates, key=lambda item: (item.confidence, overlap[item.record_id], item.record_id))
    elif len(candidates) == 1:
        record = candidates[0]
    else:
        scores = {
            candidate.record_id: sum(
                (candidate.record_id in item.supports) - (candidate.record_id in item.contradicts)
                for item in live
            )
            for candidate in candidates
        }
        best_score = max(scores.values())
        winners = [candidate for candidate in candidates if scores[candidate.record_id] == best_score]
        record = winners[0] if best_score > 0 and len(winners) == 1 else None
        reason = None if record else "no-unique-positive-outcome"
        if record:
            evidence = sorted(
                item.record_id for item in live
                if record.record_id in item.supports or record.record_id in item.contradicts
            )
    return {
        "class": query["class"], "expected_record_id": query["expected_record_id"],
        "record_id": record.record_id if record else None,
        "overlap": overlap.get(record.record_id, 0) if record else 0,
        "evidence": evidence,
        "contradictions": sorted(item.record_id for item in candidates if item is not record),
        "reliability_reason": "unique-positive-linked-outcome" if evidence else None,
        "abstention_reason": reason, "examined": len(live),
        "provenance_complete": complete_provenance(record.to_bytes()) if record else None,
    }


def evaluate(
    split: str, records: list[MemoryRecord], queries: list[dict[str, object]], policy: str
) -> dict[str, object]:
    results = [retrieve(records, query, policy) for query in queries]
    latency = []
    for _ in range(100):
        for query in queries:
            started = perf_counter_ns()
            retrieve(records, query, policy)
            latency.append(perf_counter_ns() - started)
    latency.sort()
    counts = outcomes(
        [query["expected_record_id"] for query in queries],
        [result["record_id"] for result in results],
    )
    answerable = sum(query["expected_record_id"] is not None for query in queries)
    unanswerable = len(queries) - answerable
    abstentions = counts["correct_abstention"] + counts["missed_answer"]
    returned = len(queries) - abstentions
    return {
        "split": split, "policy": policy, "outcomes": counts,
        "metrics": {
            "correct_retrieval_rate": counts["correct_retrieval"] / answerable,
            "wrong_retrieval_rate": counts["wrong_retrieval"] / answerable,
            "false_retrieval_rate": counts["false_retrieval"] / unanswerable,
            "answer_rate": returned / len(queries),
            "abstention_precision": counts["correct_abstention"] / abstentions if abstentions else None,
            "abstention_recall": counts["correct_abstention"] / unanswerable,
            "provenance_completeness": sum(r["provenance_complete"] is True for r in results) / returned,
            "records_examined": sum(result["examined"] for result in results),
            "median_latency_ns": median(latency),
            "p95_latency_ns": latency[int(len(latency) * 0.95) - 1],
            "serialized_storage_bytes": sum(len(record.to_bytes()) for record in records),
        },
        "classes": {result["class"]: result for result in results},
    }


def assert_controls(records: list[MemoryRecord], queries: list[dict[str, object]]) -> None:
    verified = queries[0]
    exact = queries[2]
    evidence = next(record for record in records if record.supports)
    without_links = [replace(record, supports=(), contradicts=()) if record is evidence else record for record in records]
    assert retrieve(without_links, verified, "outcome-provenance")["record_id"] is None
    reversed_links = [
        replace(record, supports=record.contradicts, contradicts=record.supports)
        if record is evidence else record
        for record in records
    ]
    assert retrieve(reversed_links, verified, "outcome-provenance")["record_id"] == verified["candidate_ids"][0]
    without_exact = [record for record in records if record.record_id not in exact["candidate_ids"]]
    assert retrieve(without_exact, exact, "outcome-provenance")["record_id"] is None
    assert outcomes([None], [queries[1]["candidate_ids"][0]])["false_retrieval"] == 1
    damaged = evidence.to_bytes().replace(b'"source":"inspection"', b'"source":""')
    assert not complete_provenance(damaged)
    extra = replace(records[-1], record_id="dev-extra", owner="a", frame="map-a")
    before = retrieve(records, verified, "outcome-provenance")["examined"]
    assert retrieve([*records, extra], verified, "outcome-provenance")["examined"] == before + 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("split", choices=("development", "heldout"))
    args = parser.parse_args()
    records, queries = load_fixture(args.split)
    if args.split == "development":
        assert_controls(records, queries)
    print(json.dumps([evaluate(args.split, records, queries, policy) for policy in POLICIES], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
