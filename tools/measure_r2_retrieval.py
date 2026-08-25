#!/usr/bin/env python3
"""Evaluate frozen deterministic lexical policies for CP-R2."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from statistics import median
from time import perf_counter_ns

from polybrains import MemoryRecord
from polybrains.memory import _active_records, _tokens

from measure_m2_recall import complete_provenance, outcomes


POLICIES = (
    ("v0.1", Fraction(0), Fraction(0)),
    ("normalized", Fraction(0), Fraction(0)),
    ("minimum-1/4", Fraction(1, 4), Fraction(0)),
    ("minimum-1/2", Fraction(1, 2), Fraction(0)),
    ("minimum-3/4", Fraction(3, 4), Fraction(0)),
    ("margin-1/4", Fraction(0), Fraction(1, 4)),
    ("margin-1/2", Fraction(0), Fraction(1, 2)),
)


def load_fixture(split: str) -> tuple[list[MemoryRecord], list[dict[str, object]]]:
    data = json.loads(Path(f"configs/retrieval/v02-{split}.json").read_text())
    records = [
        MemoryRecord(
            record_id=item["record_id"], owner=item["owner"], frame=item["frame"],
            source=item["source"], event_time=datetime.fromisoformat(item["event_time"]),
            write_time=datetime.fromisoformat(item["write_time"]), confidence=item["confidence"],
            payload=item["payload"].encode(), supersedes=tuple(item.get("supersedes", ())),
            reason=item.get("reason", ""),
        )
        for item in data["records"]
    ]
    return records, data["queries"]


def retrieve(
    records: list[MemoryRecord], query: dict[str, object], policy: tuple[str, Fraction, Fraction]
) -> dict[str, object]:
    name, minimum, required_margin = policy
    query_tokens = _tokens(query["text"])
    private = [
        record for record in records
        if record.owner == query["requester"] and record.frame == query["frame"]
    ]
    live = _active_records(private)
    ranked = []
    for record in live:
        record_tokens = _tokens(record.payload.decode())
        overlap = len(query_tokens & record_tokens)
        normalized = Fraction(overlap, len(query_tokens)) if query_tokens else Fraction(0)
        if overlap:
            ranked.append((normalized, overlap, record.confidence, record.event_time, record.record_id, record))
    ranked.sort(reverse=True)
    best = ranked[0] if ranked else None
    runner_score = ranked[1][0] if len(ranked) > 1 else Fraction(0)
    margin = best[0] - runner_score if best else Fraction(0)
    reason = None
    if best is None:
        reason = "no-lexical-overlap"
    elif name.startswith("minimum") and best[0] < minimum:
        reason = "below-minimum-score"
    elif name.startswith("margin") and margin < required_margin:
        reason = "below-runner-up-margin"
    record = None if reason else best[-1]
    contradictions = tuple(
        candidate[-1].record_id for candidate in ranked[1:]
        if best is not None and candidate[-1].payload != best[-1].payload
    )
    return {
        "query_id": query["query_id"], "class": query["class"],
        "expected_record_id": query["expected_record_id"],
        "record_id": record.record_id if record else None,
        "score": {
            "overlap": best[1] if best else 0,
            "query_tokens": len(query_tokens),
            "normalized": str(best[0] if best else Fraction(0)),
        },
        "runner_up_margin": str(margin),
        "evidence": [record.record_id] if record else [],
        "contradictions": list(contradictions),
        "abstention_reason": reason,
        "examined": len(live),
        "provenance_complete": complete_provenance(record.to_bytes()) if record else None,
    }


def evaluate(split: str, policy: tuple[str, Fraction, Fraction]) -> dict[str, object]:
    records, queries = load_fixture(split)
    results = [retrieve(records, query, policy) for query in queries]
    latency = []
    for _ in range(20):
        for query in queries:
            started = perf_counter_ns()
            retrieve(records, query, policy)
            latency.append(perf_counter_ns() - started)
    latency.sort()
    scores = outcomes(
        [query["expected_record_id"] for query in queries],
        [result["record_id"] for result in results],
    )
    answerable = sum(query["expected_record_id"] is not None for query in queries)
    unanswerable = len(queries) - answerable
    abstentions = scores["correct_abstention"] + scores["missed_answer"]
    returned = len(queries) - abstentions
    return {
        "split": split, "policy": policy[0], "parameters": {
            "minimum_score": str(policy[1]), "minimum_margin": str(policy[2]),
        },
        "outcomes": scores,
        "metrics": {
            "correct_retrieval_rate": scores["correct_retrieval"] / answerable,
            "wrong_retrieval_rate": scores["wrong_retrieval"] / answerable,
            "false_retrieval_rate": scores["false_retrieval"] / unanswerable,
            "answer_rate": returned / len(queries),
            "abstention_precision": scores["correct_abstention"] / abstentions if abstentions else None,
            "abstention_recall": scores["correct_abstention"] / unanswerable,
            "provenance_completeness": (
                sum(result["provenance_complete"] is True for result in results) / returned
                if returned else None
            ),
            "records_examined": sum(result["examined"] for result in results),
            "median_latency_ns": median(latency),
            "p95_latency_ns": latency[int(len(latency) * 0.95) - 1],
            "serialized_storage_bytes": sum(len(record.to_bytes()) for record in records),
        },
        "classes": {result["class"]: result for result in results},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("split", choices=("development", "heldout"))
    parser.add_argument("--policy", choices=tuple(policy[0] for policy in POLICIES))
    args = parser.parse_args()
    selected = [policy for policy in POLICIES if args.policy in (None, policy[0])]
    print(json.dumps([evaluate(args.split, policy) for policy in selected], sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
