# Additional verification — 13 October 2026

| Feature | Result | Evidence / limitation |
| --- | --- | --- |
| Live GitHub inspection | Passed | Authenticated source inspection of karpathy/minbpe; all three exports generated. Source review now uses repository documentation for limitation detection, avoiding sample training text. |
| Production configuration and build | Passed after repairs | Actual production Docker images built, including the frontend TypeScript/Vite build. Corrected spaCy/FastAPI dependency conflict, passlib/bcrypt compatibility, worker entry point and Redis DSN, production ports/mounts, API build URL, writable directories, and dynamic Nginx DNS after container replacement. |
| Production core workflow | Passed | Isolated PostgreSQL/pgvector, Redis, API, ARQ worker, frontend Nginx, and reverse proxy started successfully. Live checks passed for registration/login, PDF ingestion and review, hybrid retrieval with nonzero dense candidates, a queued pipeline from INGESTION through REPORTING, persisted reports, graph distribution, About bibliography, and IEEE/Markdown/BibTeX exports. Uses demo LLM and lexical-hash embeddings. Academic discovery and external model synthesis are outside this runtime check. |
| IEEE compilation and layout | Passed | Official Tectonic compiler downloaded into .tools/tectonic. Real GitHub export compiled and visually inspected, and a production-generated citation-bearing report compiled and rendered. Zero overfull boxes. Added xurl to prevent long links overflowing columns. Deliverable: output/pdf/live_github.pdf. |
| Gemini live model call | Awaiting user credential | User selected Gemini. No GEMINI_API_KEY or GOOGLE_API_KEY is configured. Adapter regression tests pass, but no real provider response can be obtained without a key. Add GEMINI_API_KEY securely to backend/.env.local, then run backend/.venv/Scripts/python.exe backend/scripts/verify_gemini.py. |

77 local backend regression tests passed. Temporary production services were stopped after verification; their isolated data and built images are retained. The main local application and database were preserved. Docker Desktop's existing engine was started; unrelated services were not changed.

Production verification is reproducible with examples/verification/production-runtime.yml and backend/scripts/verify_production.py. The isolated production.env contains private generated test credentials and is ignored by Git; never reuse this fixture as a public deployment configuration. The script checks endpoints on ports 18000, 18080, and 18081 and requires the test stack to be started.

IEEE compilation command: .tools/tectonic/tectonic.exe examples/verification/live_github.tex --outdir output/pdf --keep-logs. Codex's built-in compiler still requires its Windows sandbox setup; the independent compiler avoids needing any change to those settings.

Source-based drafts and proposed changes are not measured research results. Gemini's configurable default and HTTP adapter follow official documentation: https://ai.google.dev/gemini-api/docs/text-generation and https://ai.google.dev/api/interactions-api.
