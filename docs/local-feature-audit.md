# Local ResearchMind feature audit

Validated on 8 October 2026: 62 backend tests pass and the frontend production build succeeds.

The local worker now runs all eleven pipeline stages and persists progress, failures, source observations, gaps, hypotheses, experiment specifications, and reports. Restarted jobs receive a terminal failure instead of remaining stuck. Repeated discovery deduplicates papers.

The local corpus contains 126 papers, including 120 records imported from official ACL Anthology metadata for ACL 2024 and EMNLP 2024. These provide abstracts, authors, venues, years, and source links. Abstract indexing is explicitly identified; it is not a substitute for full-text review. Literature discovery searches this cached collection in local SQLite mode. Refresh the cache and import with backend/scripts/expand_nlp_corpus.py; use --cached for an offline repeat.

Reports can be generated manually or by the pipeline and exported as Markdown, BibTeX, or IEEEtran conference LaTeX. The backend does not compile PDF. References and source observations are real stored artifacts. Demo reports remain drafts and disclose unsupported claims. Recorded experiment metrics are supplied records, not independently reproduced results.

Search filters are applied before ranking, and retrieval no longer shares a database session concurrently. Evidence exposes source passages and does not invent page numbers. Knowledge graph distribution and experiment creation/run recording are covered by API regression tests.

Removed fake settings-save controls, fabricated literature comparison values, fixed-score vector matching, and unsupported verification guarantees. Runtime Diagnostics displays the actual backend configuration. Local lexical-hash retrieval requires no model download; neural retrieval and LLM synthesis require their configured dependencies and provider.

Project access is consistently restricted to the signed-in owner. The two known seeded demo projects were assigned to the provisioned local researcher account; a SQLite backup was created before importing or changing ownership.

Local sign-in: researcher@example.com. Use the provisioned password shown in the conversation or reset through the account provisioning script. Passwords are hashed in the database.

Production PostgreSQL/Redis workers and external LLM providers were not integration-tested in this local audit. Experiment designs require a separate real execution and evaluation step; the application does not manufacture results.