# CP-R2 — development selection

**Run:** 2026-08-25, before held-out evaluation  
**Fixture:** `configs/retrieval/v02-development.json`  
**Frozen candidate:** `configs/retrieval/v02-policy.json`

The unchanged v0.1 control achieved 2/4 correct retrievals, one wrong retrieval, one missed answer,
one false retrieval, and one correct abstention. Normalized overlap alone and minimum scores of
1/4 or 1/2 were identical to v0.1. Margin thresholds of 1/4 and 1/2 converted the contradictory
wrong answer to a missed answer without reducing false retrieval.

The only candidate that reduced false retrieval was minimum normalized query coverage 3/4. It
reduced false retrieval from 1/2 to 0/2 but also reduced correct retrieval from 2/4 to 1/4. That
25-percentage-point loss exceeds the registered 5-point limit, so the candidate is frozen for one
diagnostic held-out run but is already ineligible for retention. No candidate code entered the
memory core.
