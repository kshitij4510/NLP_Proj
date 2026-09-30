# Research Artifact Classification

## Artifact Types (spec §8)

ResearchMind distinguishes six artifact types. Generated content **never** silently becomes evidence.

| Type | Description | Source | Can become Evidence? |
|---|---|---|---|
| `EVIDENCE` | Verified claim mapped to a chunk | Stored paper text | Only after verification |
| `INTERPRETATION` | LLM-generated analysis | LLM output | No — requires verification |
| `HYPOTHESIS` | Proposed testable statement | Gap analysis | No — requires experiment |
| `EXPERIMENT_RESULT` | Measured metric from a run | Experiment run | Yes — measurement provenance |
| `USER_NOTE` | Researcher annotation | Human | Depends on context |
| `UNSUPPORTED_CLAIM` | Claim lacking evidence | LLM output | No — must remain tagged |

## Verification States

| Status | Meaning |
|---|---|
| `SUPPORTED` | Claim backed by ≥1 high-confidence chunk |
| `PARTIALLY_SUPPORTED` | Claim partially supported by evidence |
| `CONTRADICTED` | Evidence actively contradicts the claim |
| `INSUFFICIENT_EVIDENCE` | No relevant evidence found |
| `PENDING` | Not yet verified |

## Provenance Chain

```
Claim
  └── ClaimEvidence
        ├── paper_id → Paper
        ├── chunk_id → PaperChunk
        ├── section_id → PaperSection
        ├── page_number
        └── evidence_snippet (exact text)
```

No claim can be marked `SUPPORTED` without a corresponding `ClaimEvidence` record pointing to a real chunk.

## Citation Safety Rule

Citations are generated **exclusively** from stored `Paper` metadata:
- `title` — from paper record
- `authors` — from `paper_authors` table
- `year` — from paper record
- `venue` — from paper record
- `doi` — from paper record

An LLM is **never** asked to produce citation metadata. If metadata is missing, the citation is omitted rather than fabricated.
