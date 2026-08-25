# First memory experiment: private frames before shared memory

## Question

Does pooling episodes before retrieval create confident cross-frame errors that independent
retrieval avoids while preserving useful recall?

This experiment tests only explicit records and private episodic retrieval. It does not test
language models, embeddings, semantic consolidation, or cognition.

## Claims

- **H-M1:** independent retrieval by owner/frame, followed by explicit claim exchange, produces
  fewer cross-frame retrieval errors than one pooled store without reducing correct retrieval by
  more than 5 percentage points.
- **H-M2:** provenance/outcome-gated consolidation produces fewer false shared records than
  agreement/confidence consolidation. H-M2 is deferred until H-M1 has a working baseline; this
  experiment must not be reported as evidence for it.

## Frozen M1 fixture

Use two agents with incompatible meanings for the same lexical key:

| owner/frame | episode | confidence | expected private result |
|---|---|---:|---|
| `a/map-a` | `bank means river edge` | 0.60 | river edge |
| `b/map-b` | `bank means financial institution` | 0.99 | financial institution |

Both query `bank`. The pooled baseline ranks exact lexical overlap, then confidence, then recency,
so it returns agent B's episode to both agents. The private baseline applies the same ranking only
inside the requesting owner/frame.

The fixture also includes an unmatched query. Abstention is required when no token overlaps; an
arbitrary answer counts as a false retrieval.

## Metrics and acceptance

- **Correct retrieval rate:** correct top result / answerable queries.
- **False retrieval rate:** wrong non-abstaining top result / all queries.
- **Provenance completeness:** returned records with identity, owner, frame, source, event time,
  write time, confidence, lifecycle, and content hash / returned records.
- **Isolation:** attempts to read another owner/frame through a private store must fail.

H-M1 passes this fixture only if private retrieval has a lower false retrieval rate than pooling,
its correct retrieval rate is no more than 5 percentage points below pooling, provenance
completeness is 100%, and isolation is enforced. It fails if the pooled arm is no worse, the
private arm loses more than the margin, or the fixture cannot make either arm fail.

## Rivals and controls

- **Confidence is enough:** predicts the 0.99 episode should dominate. The incompatible-frame
  query makes that prediction wrong for agent A without treating confidence as correctness.
- **Pooling is harmless with lexical retrieval:** predicts equal arms. The shared key and distinct
  meanings are the direct control.
- **The private arm wins by using a better ranker:** both arms must use the identical deterministic
  ranker; only the candidate boundary differs.
- **The test merely checks labels:** swapping owner/frame labels must swap access, not content or
  scores.

## Exclusions

No network, model provider, vector database, opaque summarizer, automatic forgetting, shared
write, or Monty adapter. Add one only after a measured failure of this baseline justifies it.
