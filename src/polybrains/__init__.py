"""PolyBrains-AI-Memory: explicit external memory core.

Standard library only. The memory record, its lifecycle, the private episodic
store, and the deterministic retrieval baseline are re-exported here so tests
and adapters import from one place.
"""

from .memory import (
    ClaimExchange,
    EpisodicStore,
    Lifecycle,
    MemoryKind,
    MemoryRecord,
    RetrievalClaim,
    Scope,
    SharedRecord,
    SignedClaim,
    consolidate,
    consolidate_shared,
    retrieve,
    retrieve_claim,
    retrieve_framewise,
)

__all__ = [
    "ClaimExchange",
    "EpisodicStore",
    "Lifecycle",
    "MemoryKind",
    "MemoryRecord",
    "RetrievalClaim",
    "Scope",
    "SharedRecord",
    "SignedClaim",
    "consolidate",
    "consolidate_shared",
    "retrieve",
    "retrieve_claim",
    "retrieve_framewise",
]
