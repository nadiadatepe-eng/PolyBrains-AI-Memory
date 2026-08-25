from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest import TestCase

from polybrains import (
    ClaimExchange,
    EpisodicStore,
    Lifecycle,
    MemoryKind,
    MemoryRecord,
    Scope,
    SignedClaim,
    consolidate,
    retrieve,
    retrieve_claim,
    retrieve_framewise,
)


NOW = datetime(2026, 8, 23, tzinfo=timezone.utc)


def episode(record_id: str, owner: str, frame: str, text: str, confidence: float) -> MemoryRecord:
    return MemoryRecord(
        record_id=record_id,
        owner=owner,
        frame=frame,
        source="frozen-m1-fixture",
        event_time=NOW,
        write_time=NOW,
        confidence=confidence,
        payload=text.encode(),
    )


class MemoryTests(TestCase):
    def test_record_round_trip_is_deterministic_and_validated(self):
        record = episode("a1", "a", "map-a", "bank means river edge", 0.6)
        self.assertEqual(MemoryRecord.from_bytes(record.to_bytes()), record)
        self.assertEqual(MemoryRecord.from_bytes(record.to_bytes()).to_bytes(), record.to_bytes())
        with self.assertRaisesRegex(ValueError, "source is required"):
            MemoryRecord("bad", "a", "map-a", "", NOW, NOW, 0.5, b"x")
        with self.assertRaisesRegex(ValueError, "payload hash does not match"):
            MemoryRecord.from_bytes(record.to_bytes().replace(record.content_hash.encode(), b"0" * 64))

    def test_m1_private_retrieval_beats_pooling_and_preserves_abstention(self):
        a = EpisodicStore("a", "map-a")
        b = EpisodicStore("b", "map-b")
        river = episode("a1", "a", "map-a", "bank means river edge", 0.6)
        finance = episode("b1", "b", "map-b", "bank means financial institution", 0.99)
        a.append(river)
        b.append(finance)

        self.assertEqual(a.retrieve("a", "map-a", "bank"), river)
        self.assertEqual(b.retrieve("b", "map-b", "bank"), finance)
        self.assertEqual(retrieve((*a.records, *b.records), "bank"), finance)
        self.assertIsNone(a.retrieve("a", "map-a", "unmatched"))
        self.assertIsNone(retrieve((*a.records, *b.records), "unmatched"))
        with self.assertRaises(PermissionError):
            a.retrieve("b", "map-b", "bank")

    def test_supersession_and_tombstone_preserve_history(self):
        store = EpisodicStore("a", "map-a")
        original = episode("a1", "a", "map-a", "bank means river edge", 0.6)
        corrected = MemoryRecord(
            **{
                **original.__dict__,
                "record_id": "a2",
                "payload": b"bank means river shore",
                "supersedes": ("a1",),
                "reason": "correction",
            }
        )
        tombstone = MemoryRecord(
            **{
                **original.__dict__,
                "record_id": "a3",
                "payload": b"",
                "lifecycle": Lifecycle.TOMBSTONE,
                "supersedes": ("a2",),
                "reason": "deletion requested",
            }
        )
        store.append(original)
        with self.assertRaisesRegex(ValueError, "unknown record"):
            store.append(
                MemoryRecord(
                    **{**original.__dict__, "record_id": "bad", "supersedes": ("missing",), "reason": "correction"}
                )
            )
        store.append(corrected)
        self.assertEqual(store.retrieve("a", "map-a", "bank"), corrected)
        store.append(tombstone)
        self.assertIsNone(store.retrieve("a", "map-a", "bank"))
        self.assertEqual(store.records, (original, corrected, tombstone))

    def test_m3_outcome_gating_rejects_a_popular_false_claim(self):
        false = [episode(f"false-{index}", "a", "map-a", "bridge is closed", 0.99) for index in range(3)]
        true = episode("true-0", "a", "map-a", "bridge is open", 0.6)
        episodes = (*false, true)

        naive = consolidate(episodes)
        conservative = consolidate(episodes, {true.record_id})

        self.assertEqual(naive.payload, b"bridge is closed")
        self.assertEqual(conservative.payload, b"bridge is open")
        self.assertEqual((naive.kind, conservative.kind), (MemoryKind.SEMANTIC, MemoryKind.SEMANTIC))
        self.assertEqual(set(naive.supports + naive.contradicts), {record.record_id for record in episodes})
        self.assertEqual(set(conservative.supports + conservative.contradicts), {record.record_id for record in episodes})
        self.assertEqual(naive.contradicts, (true.record_id,))
        self.assertEqual(set(conservative.contradicts), {record.record_id for record in false})
        self.assertIsNone(consolidate(episodes, set()))

    def test_m4_framewise_claims_preserve_disagreement_and_filters(self):
        a = EpisodicStore("a", "map-a")
        b = EpisodicStore("b", "map-b")
        river = episode("a1", "a", "map-a", "bank means river edge", 0.6)
        finance = episode("b1", "b", "map-b", "bank means financial institution", 0.99)
        a.append(river)
        b.append(finance)

        claims = retrieve_framewise((a, b), "bank")
        pooled = tuple(
            retrieve_claim((*a.records, *b.records), "bank", owner, frame)
            for owner, frame in (("a", "map-a"), ("b", "map-b"))
        )

        self.assertEqual(tuple(claim.record for claim in claims), (river, finance))
        self.assertEqual(tuple(claim.record for claim in pooled), (finance, finance))
        self.assertEqual(tuple((claim.score, claim.examined) for claim in claims), ((1, 1), (1, 1)))
        self.assertEqual(sum(claim.examined for claim in pooled), 4)
        self.assertEqual(claims[0].contradictions, (finance,))
        self.assertEqual(claims[1].contradictions, (river,))
        self.assertTrue(all(claim.abstained for claim in retrieve_framewise((a, b), "unmatched")))
        self.assertTrue(retrieve_claim(a.records, "bank", "a", "map-a", at=NOW - timedelta(seconds=1)).abstained)
        self.assertTrue(retrieve_claim(a.records, "bank", "a", "map-a", source="other").abstained)

    def test_m5_lifecycle_preserves_history_and_deletes_protected_payload(self):
        store = EpisodicStore("a", "map-a")
        stale = episode("stale", "a", "map-a", "bridge is closed", 0.7)
        corrected = MemoryRecord(
            **{
                **stale.__dict__,
                "record_id": "corrected",
                "payload": b"bridge is open",
                "supersedes": (stale.record_id,),
                "reason": "observed bridge open",
            }
        )
        store.append(stale)
        store.append(corrected)
        self.assertEqual(store.retrieve("a", "map-a", "bridge"), corrected)

        archived = store.transition(
            corrected.record_id, "archived", Lifecycle.ARCHIVED, "decay: older than retention window", NOW
        )
        forgotten_source = episode("forget-me", "a", "map-a", "temporary preference", 0.5)
        store.append(forgotten_source)
        forgotten = store.transition(
            forgotten_source.record_id, "forgotten", Lifecycle.FORGOTTEN, "retention policy", NOW
        )
        secret = episode("secret", "a", "map-a", "privacy secret-731", 0.5)
        store.append(secret)
        before_delete = store.payload_bytes
        deleted = store.delete(secret.record_id, "deleted", "privacy request", NOW)

        self.assertIsNone(store.retrieve("a", "map-a", "bridge"))
        self.assertIn(stale, store.records)
        self.assertEqual((archived.lifecycle, forgotten.lifecycle, deleted.lifecycle), (
            Lifecycle.ARCHIVED,
            Lifecycle.FORGOTTEN,
            Lifecycle.TOMBSTONE,
        ))
        self.assertTrue(archived.payload)
        self.assertFalse(forgotten.payload)
        self.assertNotIn(secret, store.records)
        self.assertFalse(any(b"secret-731" in record.payload for record in store.records))
        self.assertEqual(store.payload_bytes, before_delete - len(secret.payload))
        self.assertEqual(MemoryRecord.from_bytes(deleted.to_bytes()).reason, "privacy request")
        with self.assertRaisesRegex(ValueError, "reason"):
            MemoryRecord(**{**stale.__dict__, "record_id": "unexplained", "supersedes": (stale.record_id,)})
        with self.assertRaisesRegex(ValueError, "already superseded"):
            store.append(
                MemoryRecord(
                    **{**stale.__dict__, "record_id": "late", "supersedes": (stale.record_id,), "reason": "late correction"}
                )
            )

        evidence = (
            episode("e1", "a", "map-a", "stable fact", 0.7),
            episode("e2", "a", "map-a", "stable fact", 0.8),
        )
        compressed = consolidate(evidence, {"e1", "e2"})
        self.assertEqual(set(compressed.supports), {"e1", "e2"})

    def test_m6_signed_claims_block_correlated_false_consolidation(self):
        members = tuple("abcdef")
        keys = {member: f"key-{member}".encode() for member in members}
        exchange = ClaimExchange(members, keys)
        false_records = tuple(
            MemoryRecord(
                **{
                    **episode(f"false-{author}", author, f"map-{author}", "bridge is closed", 0.99).__dict__,
                    "source": "correlated-prior",
                }
            )
            for author in "abc"
        )
        true_record = MemoryRecord(
            **{
                **episode("true-d", "d", "map-d", "bridge is open", 0.6).__dict__,
                "source": "observed-outcome",
            }
        )
        shared_claims = tuple(
            SignedClaim.from_record(record, "bridge", Scope.SHARED, keys[record.owner])
            for record in (*false_records, true_record)
        ) + (
            SignedClaim.abstain(
                "e:abstain", "e", "map-e", "no-observation", "bridge", Scope.SHARED, keys["e"]
            ),
        )
        for claim in shared_claims:
            exchange.publish(claim)

        private = SignedClaim.from_record(
            episode("private-a", "a", "map-a", "private note", 0.5), "note", Scope.PRIVATE, keys["a"]
        )
        public = SignedClaim.from_record(
            episode("public-d", "d", "map-d", "public note", 0.5), "note", Scope.PUBLIC, keys["d"]
        )
        exchange.publish(private)
        exchange.publish(public)

        before = exchange.claims
        pooled = exchange.consolidate("bridge", "pooled")
        majority = exchange.consolidate("bridge", "majority")
        confidence = exchange.consolidate("bridge", "confidence")
        before_outcome = exchange.consolidate("bridge", "conservative")
        conservative = exchange.consolidate("bridge", "conservative", {true_record.record_id})

        self.assertEqual({record.payload for record in pooled}, {b"bridge is closed", b"bridge is open"})
        self.assertEqual(majority[0].payload, b"bridge is closed")
        self.assertEqual(confidence[0].payload, b"bridge is closed")
        self.assertEqual(before_outcome, ())
        self.assertEqual(conservative[0].payload, b"bridge is open")
        self.assertEqual(exchange.claims, before)
        self.assertEqual(len(exchange.agreement("b", "bridge", b"bridge is closed")), 3)
        self.assertEqual(len(exchange.contradictions("b", shared_claims[0].claim_id)), 1)
        self.assertEqual(exchange.contradictions("b", "e:abstain"), ())
        self.assertEqual(exchange.silent(members, "bridge"), frozenset({"f"}))
        self.assertEqual(exchange.silent(members, "note"), frozenset(members))
        self.assertEqual(sum(claim.abstained for claim in exchange.claims), 1)
        self.assertEqual({claim.source for claim in shared_claims[:3]}, {"correlated-prior"})
        self.assertNotIn(private, exchange.read("b"))
        self.assertIn(private, exchange.read("a"))
        self.assertEqual(exchange.read("outsider"), (public,))
        self.assertTrue(all(len(record.supports) + len(record.contradicts) == 4 for record in (*pooled, *majority, *confidence, *conservative)))
        self.assertEqual(
            tuple(6 if any(record.payload == b"bridge is closed" for record in arm) else 0 for arm in (pooled, majority, confidence, conservative)),
            (6, 6, 6, 0),
        )
        self.assertEqual(
            tuple(int(any(record.payload == b"bridge is open" for record in arm)) for arm in (pooled, majority, confidence, conservative)),
            (1, 0, 0, 1),
        )
        forged = replace(shared_claims[0], claim_id="a:forged", subject="forged", payload=b"bridge is open")
        with self.assertRaises(PermissionError):
            exchange.publish(forged)
        self.assertEqual(exchange.consolidate("forged", "pooled"), ())

    def test_m7_cutoff_decay_removes_stale_errors_without_losing_fresh_recall(self):
        cutoff = NOW - timedelta(days=5)
        old = tuple(
            replace(
                episode(f"old-{cue}", "a", "map-a", f"{cue} obsolete", 0.8),
                event_time=NOW - timedelta(days=10),
                write_time=NOW - timedelta(days=10),
            )
            for cue in ("alpha", "beta")
        )
        fresh = tuple(
            episode(f"fresh-{cue}", "a", "map-a", f"{cue} current", 0.8)
            for cue in ("gamma", "delta")
        )
        boundary = replace(episode("boundary", "a", "map-a", "epsilon current", 0.8), event_time=cutoff)
        baseline = EpisodicStore("a", "map-a")
        decayed = EpisodicStore("a", "map-a")
        for record in (*old, *fresh, boundary):
            baseline.append(record)
            decayed.append(record)

        markers = decayed.decay(cutoff, "decay: five-day retention", NOW)
        queries = ("alpha", "beta", "gamma", "delta")
        baseline_results = tuple(baseline.retrieve("a", "map-a", query) for query in queries)
        decay_results = tuple(decayed.retrieve("a", "map-a", query) for query in queries)

        self.assertEqual(
            (
                sum(result in fresh for result in baseline_results),
                sum(result in old for result in baseline_results),
                sum(result is not None for result in baseline_results),
            ),
            (2, 2, 4),
        )
        self.assertEqual(
            (
                sum(result in fresh for result in decay_results),
                sum(result in old for result in decay_results),
                sum(result is not None for result in decay_results),
            ),
            (2, 0, 2),
        )
        self.assertEqual(len(markers), 2)
        self.assertTrue(all(marker.reason == "decay: five-day retention" for marker in markers))
        self.assertTrue(all(record in decayed.records for record in old))
        self.assertEqual(decayed.retrieve("a", "map-a", "epsilon"), boundary)

        collision = EpisodicStore("a", "map-a")
        for record in (*old, episode("decay-old-beta", "a", "map-a", "reserved marker", 0.5)):
            collision.append(record)
        before_collision = collision.records
        with self.assertRaisesRegex(ValueError, "marker record_id"):
            collision.decay(cutoff, "decay: five-day retention", NOW)
        self.assertEqual(collision.records, before_collision)
