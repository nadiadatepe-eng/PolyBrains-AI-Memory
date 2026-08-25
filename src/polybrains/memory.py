"""Model-independent, append-only episodic memory."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable


class MemoryKind(str, Enum):
    SHORT_TERM = "short-term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    LONG_TERM = "long-term"


class Lifecycle(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    FORGOTTEN = "forgotten"
    TOMBSTONE = "tombstone"


class Scope(str, Enum):
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must include a timezone")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class MemoryRecord:
    record_id: str
    owner: str
    frame: str
    source: str
    event_time: datetime
    write_time: datetime
    confidence: float
    payload: bytes
    kind: MemoryKind = MemoryKind.EPISODIC
    lifecycle: Lifecycle = Lifecycle.ACTIVE
    supports: tuple[str, ...] = ()
    contradicts: tuple[str, ...] = ()
    supersedes: tuple[str, ...] = ()
    reason: str = ""
    version: int = 1

    def __post_init__(self) -> None:
        for name in ("record_id", "owner", "frame", "source"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if self.version != 1:
            raise ValueError("unsupported record version")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if (self.lifecycle is not Lifecycle.ACTIVE or self.supersedes) and not self.reason.strip():
            raise ValueError("lifecycle transitions require a reason")
        if self.lifecycle is not Lifecycle.ACTIVE and not self.supersedes:
            raise ValueError("a lifecycle marker must identify the record it changes")
        if self.lifecycle in (Lifecycle.FORGOTTEN, Lifecycle.TOMBSTONE) and self.payload:
            raise ValueError("forgotten and deleted records cannot retain payload")
        _utc(self.event_time)
        _utc(self.write_time)

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.payload).hexdigest()

    def to_bytes(self) -> bytes:
        data = {
            "confidence": self.confidence,
            "content_hash": self.content_hash,
            "contradicts": list(self.contradicts),
            "event_time": _utc(self.event_time).isoformat(),
            "frame": self.frame,
            "kind": self.kind.value,
            "lifecycle": self.lifecycle.value,
            "owner": self.owner,
            "payload": base64.b64encode(self.payload).decode("ascii"),
            "record_id": self.record_id,
            "reason": self.reason,
            "source": self.source,
            "supersedes": list(self.supersedes),
            "supports": list(self.supports),
            "version": self.version,
            "write_time": _utc(self.write_time).isoformat(),
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()

    @classmethod
    def from_bytes(cls, raw: bytes) -> "MemoryRecord":
        data = json.loads(raw)
        expected_hash = data.pop("content_hash")
        data["payload"] = base64.b64decode(data["payload"], validate=True)
        for name in ("event_time", "write_time"):
            data[name] = datetime.fromisoformat(data[name])
        for name in ("supports", "contradicts", "supersedes"):
            data[name] = tuple(data[name])
        data["kind"] = MemoryKind(data["kind"])
        data["lifecycle"] = Lifecycle(data["lifecycle"])
        record = cls(**data)
        if record.content_hash != expected_hash:
            raise ValueError("payload hash does not match")
        return record


@dataclass(frozen=True)
class RetrievalClaim:
    owner: str
    frame: str
    record: MemoryRecord | None
    score: int
    examined: int
    contradictions: tuple[MemoryRecord, ...] = ()

    @property
    def abstained(self) -> bool:
        return self.record is None


@dataclass(frozen=True)
class SignedClaim:
    claim_id: str
    author: str
    frame: str
    source: str
    subject: str
    payload: bytes | None
    confidence: float
    evidence: tuple[str, ...]
    scope: Scope
    abstained: bool
    signature: str = ""

    def __post_init__(self) -> None:
        if not self.claim_id or not self.author or not self.frame or not self.source or not self.subject:
            raise ValueError("claim identity and provenance are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.abstained != (self.payload is None) or (self.abstained and self.evidence):
            raise ValueError("abstention requires no payload or evidence")
        if not self.abstained and not self.evidence:
            raise ValueError("a claim must reference evidence")

    def signing_bytes(self) -> bytes:
        return json.dumps(
            {
                "abstained": self.abstained,
                "author": self.author,
                "claim_id": self.claim_id,
                "confidence": self.confidence,
                "evidence": list(self.evidence),
                "frame": self.frame,
                "payload": None if self.payload is None else base64.b64encode(self.payload).decode("ascii"),
                "scope": self.scope.value,
                "source": self.source,
                "subject": self.subject,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

    @classmethod
    def from_record(cls, record: MemoryRecord, subject: str, scope: Scope, key: bytes) -> SignedClaim:
        claim = cls(
            f"{record.owner}:{record.record_id}",
            record.owner,
            record.frame,
            record.source,
            subject,
            record.payload,
            record.confidence,
            (record.record_id,),
            scope,
            False,
        )
        return replace(claim, signature=hmac.new(key, claim.signing_bytes(), hashlib.sha256).hexdigest())

    @classmethod
    def abstain(
        cls, claim_id: str, author: str, frame: str, source: str, subject: str, scope: Scope, key: bytes
    ) -> SignedClaim:
        claim = cls(claim_id, author, frame, source, subject, None, 0.0, (), scope, True)
        return replace(claim, signature=hmac.new(key, claim.signing_bytes(), hashlib.sha256).hexdigest())


@dataclass(frozen=True)
class SharedRecord:
    policy: str
    payload: bytes
    supports: tuple[str, ...]
    contradicts: tuple[str, ...]


class ClaimExchange:
    """Authenticated claim exchange; private stores never cross this boundary."""

    def __init__(self, members: Iterable[str], keys: dict[str, bytes]) -> None:
        self.members = frozenset(members)
        if self.members != keys.keys():
            raise ValueError("each member requires exactly one verification key")
        self._keys = dict(keys)
        self._claims: list[SignedClaim] = []

    @property
    def claims(self) -> tuple[SignedClaim, ...]:
        return tuple(self._claims)

    def publish(self, claim: SignedClaim) -> None:
        key = self._keys.get(claim.author)
        if key is None or not hmac.compare_digest(
            claim.signature, hmac.new(key, claim.signing_bytes(), hashlib.sha256).hexdigest()
        ):
            raise PermissionError("claim signature is invalid")
        if any(existing.claim_id == claim.claim_id for existing in self._claims):
            raise ValueError("claim_id already exists")
        self._claims.append(claim)

    def read(self, requester: str) -> tuple[SignedClaim, ...]:
        return tuple(
            claim
            for claim in self._claims
            if claim.scope is Scope.PUBLIC
            or claim.author == requester
            or (claim.scope is Scope.SHARED and requester in self.members)
        )

    def agreement(self, requester: str, subject: str, payload: bytes) -> tuple[SignedClaim, ...]:
        return tuple(
            claim
            for claim in self.read(requester)
            if claim.subject == subject and claim.payload == payload and not claim.abstained
        )

    def contradictions(self, requester: str, claim_id: str) -> tuple[SignedClaim, ...]:
        visible = self.read(requester)
        claim = next(claim for claim in visible if claim.claim_id == claim_id)
        return tuple(
            other
            for other in visible
            if other.subject == claim.subject and not other.abstained and other.payload != claim.payload
        )

    def silent(self, expected: Iterable[str]) -> frozenset[str]:
        return frozenset(expected) - {claim.author for claim in self._claims}


def consolidate_shared(
    claims: Iterable[SignedClaim], policy: str, verified_evidence: Iterable[str] = ()
) -> tuple[SharedRecord, ...]:
    claims = [claim for claim in claims if not claim.abstained]
    if len({claim.subject for claim in claims}) > 1:
        raise ValueError("shared consolidation requires one subject")
    groups: dict[bytes, list[SignedClaim]] = {}
    for claim in claims:
        groups.setdefault(claim.payload, []).append(claim)
    if not groups:
        return ()
    verified = set(verified_evidence)
    if policy == "pooled":
        chosen = list(groups.values())
    elif policy == "majority":
        chosen = [max(groups.values(), key=lambda group: (len(group), max(c.confidence for c in group), group[0].payload))]
    elif policy == "confidence":
        winner = max(claims, key=lambda claim: (claim.confidence, claim.claim_id))
        chosen = [groups[winner.payload]]
    elif policy == "conservative":
        eligible = [group for group in groups.values() if any(verified & set(claim.evidence) for claim in group)]
        if not eligible:
            return ()
        chosen = [
            max(
                eligible,
                key=lambda group: (
                    sum(len(verified & set(claim.evidence)) for claim in group),
                    len(group),
                    max(claim.confidence for claim in group),
                    group[0].payload,
                ),
            )
        ]
    else:
        raise ValueError("unknown shared consolidation policy")
    return tuple(
        SharedRecord(
            policy,
            group[0].payload,
            tuple(sorted(claim.claim_id for claim in group)),
            tuple(sorted(claim.claim_id for claim in claims if claim.payload != group[0].payload)),
        )
        for group in chosen
    )


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"\w+", value.casefold()))


def _rank(
    records: Iterable[MemoryRecord],
    query: str,
    *,
    at: datetime | None = None,
    source: str | None = None,
) -> tuple[MemoryRecord | None, int, int]:
    query_tokens = _tokens(query)
    live = list(records)
    hidden = {target for record in live for target in record.supersedes}
    candidates = []
    examined = 0
    for record in live:
        if (
            record.lifecycle is not Lifecycle.ACTIVE
            or record.record_id in hidden
            or (at is not None and _utc(record.event_time) > _utc(at))
            or (source is not None and record.source != source)
        ):
            continue
        examined += 1
        overlap = len(query_tokens & _tokens(record.payload.decode("utf-8")))
        if overlap:
            candidates.append((overlap, record.confidence, _utc(record.event_time), record.record_id, record))
    best = max(candidates, default=(0, None, None, None, None))
    return best[-1], best[0], examined


def retrieve(
    records: Iterable[MemoryRecord],
    query: str,
    *,
    at: datetime | None = None,
    source: str | None = None,
) -> MemoryRecord | None:
    """Return the deterministic lexical top match, or abstain."""
    return _rank(records, query, at=at, source=source)[0]


def retrieve_claim(
    records: Iterable[MemoryRecord],
    query: str,
    owner: str,
    frame: str,
    *,
    at: datetime | None = None,
    source: str | None = None,
) -> RetrievalClaim:
    record, score, examined = _rank(records, query, at=at, source=source)
    return RetrievalClaim(owner, frame, record, score, examined)


def retrieve_framewise(
    stores: Iterable[EpisodicStore],
    query: str,
    *,
    at: datetime | None = None,
    source: str | None = None,
) -> tuple[RetrievalClaim, ...]:
    """Retrieve privately, then exchange claims without choosing a global winner."""
    claims = []
    for store in stores:
        claims.append(retrieve_claim(store.records, query, store.owner, store.frame, at=at, source=source))
    return tuple(
        RetrievalClaim(
            claim.owner,
            claim.frame,
            claim.record,
            claim.score,
            claim.examined,
            tuple(
                other.record
                for other in claims
                if claim.record is not None
                and other.record is not None
                and other.record.payload != claim.record.payload
            ),
        )
        for claim in claims
    )


def consolidate(
    records: Iterable[MemoryRecord], verified_outcomes: Iterable[str] | None = None
) -> MemoryRecord | None:
    """Consolidate exact claims by agreement, or only claims with a verified outcome."""
    records = list(records)
    hidden = {target for record in records for target in record.supersedes}
    episodes = [
        record
        for record in records
        if record.kind is MemoryKind.EPISODIC
        and record.lifecycle is Lifecycle.ACTIVE
        and record.record_id not in hidden
    ]
    if not episodes:
        return None
    if len({(record.owner, record.frame) for record in episodes}) != 1:
        raise ValueError("consolidation requires one owner and frame")

    verified = None if verified_outcomes is None else set(verified_outcomes)
    if verified is not None and not verified <= {record.record_id for record in episodes}:
        raise ValueError("verified outcome references an unknown active episode")
    groups: dict[bytes, list[MemoryRecord]] = {}
    for record in episodes:
        groups.setdefault(record.payload, []).append(record)
    eligible = list(groups.values()) if verified is None else [group for group in groups.values() if verified & {r.record_id for r in group}]
    if not eligible:
        return None

    chosen = max(
        eligible,
        key=lambda group: (
            0 if verified is None else len(verified & {record.record_id for record in group}),
            len(group),
            max(record.confidence for record in group),
            group[0].payload,
        ),
    )
    supports = tuple(sorted(record.record_id for record in chosen))
    contradicts = tuple(sorted(record.record_id for record in episodes if record not in chosen))
    policy = "agreement" if verified is None else "outcome"
    owner, frame = episodes[0].owner, episodes[0].frame
    return MemoryRecord(
        record_id=f"semantic-{hashlib.sha256((policy + '|'.join(supports)).encode()).hexdigest()[:16]}",
        owner=owner,
        frame=frame,
        source=f"consolidation:{policy}",
        event_time=max(record.event_time for record in chosen),
        write_time=max(record.write_time for record in episodes),
        confidence=max(record.confidence for record in chosen),
        payload=chosen[0].payload,
        kind=MemoryKind.SEMANTIC,
        supports=supports,
        contradicts=contradicts,
    )


class EpisodicStore:
    """An append-only store owned by exactly one agent and reference frame."""

    def __init__(self, owner: str, frame: str) -> None:
        if not owner or not frame:
            raise ValueError("owner and frame are required")
        self.owner = owner
        self.frame = frame
        self._records: list[MemoryRecord] = []
        self._ids: set[str] = set()

    @property
    def records(self) -> tuple[MemoryRecord, ...]:
        return tuple(self._records)

    @property
    def payload_bytes(self) -> int:
        return sum(len(record.payload) for record in self._records)

    def append(self, record: MemoryRecord) -> None:
        if (record.owner, record.frame) != (self.owner, self.frame):
            raise PermissionError("record belongs to another private store")
        if record.record_id in self._ids:
            raise ValueError("record_id already exists")
        if any(target not in self._ids for target in record.supersedes):
            raise ValueError("cannot supersede an unknown record")
        hidden = {target for existing in self._records for target in existing.supersedes}
        if any(target in hidden for target in record.supersedes):
            raise ValueError("cannot transition an already superseded record")
        self._records.append(record)
        self._ids.add(record.record_id)

    def transition(
        self,
        record_id: str,
        marker_id: str,
        lifecycle: Lifecycle,
        reason: str,
        write_time: datetime,
    ) -> MemoryRecord:
        if lifecycle not in (Lifecycle.ARCHIVED, Lifecycle.FORGOTTEN):
            raise ValueError("transition supports archived or forgotten lifecycle")
        try:
            record = next(record for record in self._records if record.record_id == record_id)
        except StopIteration:
            raise ValueError("cannot transition an unknown record") from None
        marker = replace(
            record,
            record_id=marker_id,
            write_time=write_time,
            lifecycle=lifecycle,
            payload=b"" if lifecycle is Lifecycle.FORGOTTEN else record.payload,
            supersedes=(record_id,),
            reason=reason,
        )
        self.append(marker)
        return marker

    def decay(self, before: datetime, reason: str, write_time: datetime) -> tuple[MemoryRecord, ...]:
        cutoff = _utc(before)
        hidden = {target for record in self._records for target in record.supersedes}
        stale = [
            record
            for record in self._records
            if record.kind is MemoryKind.EPISODIC
            and record.lifecycle is Lifecycle.ACTIVE
            and record.record_id not in hidden
            and _utc(record.event_time) < cutoff
        ]
        return tuple(
            self.transition(record.record_id, f"decay-{record.record_id}", Lifecycle.ARCHIVED, reason, write_time)
            for record in stale
        )

    def delete(self, record_id: str, tombstone_id: str, reason: str, write_time: datetime) -> MemoryRecord:
        try:
            record = next(record for record in self._records if record.record_id == record_id)
        except StopIteration:
            raise ValueError("cannot delete an unknown record") from None
        tombstone = replace(
            record,
            record_id=tombstone_id,
            write_time=write_time,
            lifecycle=Lifecycle.TOMBSTONE,
            payload=b"",
            supersedes=(record_id,),
            reason=reason,
        )
        self.append(tombstone)
        self._records.remove(record)
        return tombstone

    def retrieve(
        self,
        requester: str,
        frame: str,
        query: str,
        *,
        at: datetime | None = None,
        source: str | None = None,
    ) -> MemoryRecord | None:
        if (requester, frame) != (self.owner, self.frame):
            raise PermissionError("private memory is isolated by owner and frame")
        return retrieve(self._records, query, at=at, source=source)
