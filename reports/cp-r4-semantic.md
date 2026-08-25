# CP-R4 — conditional semantic retrieval

**Run:** 2026-08-25  
**Pre-registration:** commits `d43b794` and `fbbedc9`  
**Model:** `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a24`, CPU, safetensors  
**Selected on development:** cosine threshold 0.55

The frozen semantic candidate passed every registered margin. It recovered all three replication
paraphrases and increased correct retrieval from 2/4 to 3/4 on every seed. False retrieval was
unchanged on seeds 11 and 37 and fell from 1/2 to 0/2 on seed 23. Wrong retrieval stayed 1/4: the
high-confidence contradictory prior remained wrong, so semantic similarity did not silently turn
confidence into correctness.

| seed | correct | false | paraphrase | median / p95 query | index time / bytes |
|---:|---:|---:|---|---:|---:|
| 11 | 3/4 | 1/2 | correct | 5.165 / 13.148 ms | 12.524 ms / 12,288 B |
| 23 | 3/4 | 0/2 | correct | 5.521 / 7.217 ms | 8.272 ms / 12,288 B |
| 37 | 3/4 | 1/2 | correct | 5.327 / 8.472 ms | 10.734 ms / 12,288 B |

Provenance was 100%, examined records stayed 31, every owner/frame swap preserved returned IDs and
abstention reasons, and repeated encodes returned identical IDs. Cached model loading took 0.174
seconds. The model cache used 91,579,245 bytes and the isolated CPU environment 1,290,060,543
bytes, both below their frozen ceilings. A first default resolver path was stopped before install
because GPU/CUDA wheels exceeded 1.95 GB compressed; the measured candidate uses CPU-only Torch.

Embeddings remain candidate generation in `tools/measure_r4_semantic.py`; deterministic private-
frame, lifecycle, supersession, provenance, contradiction, and abstention handling remain outside
the model. No vector database, network runtime, generated answer, or dependency was added to the
standard-library memory core. The optional semantic benchmark is retained for CP-R5 rather than
made mandatory.

Method references: [Sentence Transformers semantic search](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html)
and [pinned model repository](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/1110a24).
