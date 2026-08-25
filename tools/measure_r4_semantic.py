#!/usr/bin/env python3
"""Evaluate the pre-registered CP-R4 semantic candidate outside the core."""

from __future__ import annotations

import json
import os
from pathlib import Path
from statistics import median
from time import perf_counter_ns

import numpy as np
from sentence_transformers import SentenceTransformer

from polybrains.memory import _active_records

from measure_m2_recall import complete_provenance, outcomes
from measure_r2_retrieval import POLICIES, evaluate_fixture, load_fixture
from measure_r3_replication import fixture, swapped


CONFIG = json.loads(Path("configs/retrieval/v02-semantic.json").read_text())
MODEL_CACHE = Path(os.environ.get("POLYBRAINS_R4_CACHE", "/tmp/polybrains-r4-model"))


def filtered(records, query):
    return _active_records(
        record for record in records
        if record.owner == query["requester"] and record.frame == query["frame"]
    )


def evaluate_semantic(name, records, queries, model, threshold):
    index_started = perf_counter_ns()
    embeddings = model.encode_document(
        [record.payload.decode() for record in records], normalize_embeddings=True,
        convert_to_numpy=True, show_progress_bar=False,
    )
    index_ns = perf_counter_ns() - index_started
    by_id = {record.record_id: index for index, record in enumerate(records)}

    def run_query(query):
        live = filtered(records, query)
        started = perf_counter_ns()
        query_embedding = model.encode_query(
            query["text"], normalize_embeddings=True, convert_to_numpy=True,
            show_progress_bar=False,
        )
        scores = sorted(
            ((float(np.dot(query_embedding, embeddings[by_id[record.record_id]])), record) for record in live),
            key=lambda item: (item[0], item[1].confidence, item[1].record_id), reverse=True,
        )
        elapsed = perf_counter_ns() - started
        best = scores[0] if scores else None
        runner = scores[1] if len(scores) > 1 else None
        record = best[1] if best and best[0] >= threshold else None
        reason = None if record else ("below-semantic-threshold" if best else "no-candidate")
        return {
            "class": query["class"], "expected_record_id": query["expected_record_id"],
            "record_id": record.record_id if record else None,
            "score": best[0] if best else None,
            "runner_up_score": runner[0] if runner else None,
            "evidence": [record.record_id] if record else [],
            "contradictions": [
                candidate.record_id for _, candidate in scores[1:2]
                if best and candidate.payload != best[1].payload
            ],
            "abstention_reason": reason, "examined": len(live), "latency_ns": elapsed,
            "provenance_complete": complete_provenance(record.to_bytes()) if record else None,
        }

    results = [run_query(query) for query in queries]
    repeated = [run_query(query) for query in queries]
    assert [result["record_id"] for result in results] == [result["record_id"] for result in repeated]
    counts = outcomes(
        [query["expected_record_id"] for query in queries],
        [result["record_id"] for result in results],
    )
    answerable = sum(query["expected_record_id"] is not None for query in queries)
    unanswerable = len(queries) - answerable
    abstentions = counts["correct_abstention"] + counts["missed_answer"]
    returned = len(queries) - abstentions
    latency = sorted(result["latency_ns"] for result in results + repeated)
    return {
        "split": name, "threshold": threshold, "outcomes": counts,
        "metrics": {
            "correct_retrieval_rate": counts["correct_retrieval"] / answerable,
            "wrong_retrieval_rate": counts["wrong_retrieval"] / answerable,
            "false_retrieval_rate": counts["false_retrieval"] / unanswerable,
            "answer_rate": returned / len(queries),
            "abstention_precision": counts["correct_abstention"] / abstentions if abstentions else None,
            "abstention_recall": counts["correct_abstention"] / unanswerable,
            "provenance_completeness": sum(r["provenance_complete"] is True for r in results) / returned if returned else None,
            "records_examined": sum(result["examined"] for result in results),
            "median_query_latency_ms": median(latency) / 1_000_000,
            "p95_query_latency_ms": latency[int(len(latency) * 0.95) - 1] / 1_000_000,
            "index_time_ms": index_ns / 1_000_000,
            "index_storage_bytes": embeddings.nbytes,
        },
        "classes": {result["class"]: result for result in results},
        "repeat_returned_ids_match": True,
    }


def directory_bytes(path):
    return sum(item.lstat().st_size for item in path.rglob("*") if not item.is_dir())


def main():
    load_started = perf_counter_ns()
    model = SentenceTransformer(
        CONFIG["model"], revision=CONFIG["revision"], cache_folder=str(MODEL_CACHE),
        model_kwargs={"use_safetensors": True}, device="cpu",
    )
    load_seconds = (perf_counter_ns() - load_started) / 1_000_000_000
    records, queries = load_fixture("development")
    control = evaluate_fixture("development", records, queries, POLICIES[0])
    candidates = [evaluate_semantic("development", records, queries, model, value) for value in CONFIG["development_threshold_grid"]]
    eligible = [
        result for result in candidates
        if result["metrics"]["correct_retrieval_rate"] >= control["metrics"]["correct_retrieval_rate"]
        and result["metrics"]["false_retrieval_rate"] <= control["metrics"]["false_retrieval_rate"]
        and result["metrics"]["wrong_retrieval_rate"] <= control["metrics"]["wrong_retrieval_rate"]
    ]
    if not eligible:
        print(json.dumps({"status": "no-development-candidate", "control": control, "candidates": candidates}, indent=2, sort_keys=True))
        return
    chosen = max(
        eligible,
        key=lambda result: (
            result["classes"]["answerable-paraphrase"]["record_id"] == result["classes"]["answerable-paraphrase"]["expected_record_id"],
            -result["metrics"]["false_retrieval_rate"], result["metrics"]["correct_retrieval_rate"], -result["threshold"],
        ),
    )
    replication = json.loads(Path("configs/retrieval/v02-replication.json").read_text())
    runs = []
    for seed in replication["seeds"]:
        seed_records, seed_queries = fixture(seed, replication)
        result = evaluate_semantic(f"seed-{seed}", seed_records, seed_queries, model, chosen["threshold"])
        swap_records, swap_queries = swapped(seed_records, seed_queries, replication["owner_frame_swap"])
        swap_result = evaluate_semantic(f"seed-{seed}-swapped", swap_records, swap_queries, model, chosen["threshold"])
        result["owner_frame_swap_match"] = all(
            (details["record_id"], details["abstention_reason"])
            == (
                swap_result["classes"][class_name]["record_id"],
                swap_result["classes"][class_name]["abstention_reason"],
            )
            for class_name, details in result["classes"].items()
        )
        runs.append(result)
    print(json.dumps({
        "status": "evaluated", "model": CONFIG["model"], "revision": CONFIG["revision"],
        "model_load_seconds": load_seconds, "model_cache_bytes": directory_bytes(MODEL_CACHE),
        "development_control": control, "development_candidates": candidates,
        "chosen_threshold": chosen["threshold"], "replication": runs,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
