# ResearchMind: complete demonstration with real papers

## Materials and verified scope

Use the running app at http://localhost:5173. API documentation is at http://localhost:8001/docs.
Demo login: researcher@example.com / ResearchPass123.

The following original PDFs were downloaded without modification and checked for searchable text:

| Local file under data/demo-papers | Paper | Official source |
| --- | --- | --- |
| lewis_2020_rag.pdf | Patrick Lewis et al., Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks, NeurIPS 2020 (16 pages) | https://papers.neurips.cc/paper/2020/file/6b493230205f780e1bc26945df7481e5-Paper.pdf |
| asai_2023_self_rag.pdf | Akari Asai et al., Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection (30 pages) | https://arxiv.org/abs/2310.11511 |
| min_2023_factscore.pdf | Sewon Min et al., FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation (25 pages) | https://arxiv.org/abs/2305.14251 |

The first paper is sufficient for PDF ingestion, review, search, and exports. Use all three in one project for a richer corpus demonstration. Reading these papers does not execute or reproduce their research experiments.

Current local mode uses SQLite, in-process jobs, demo synthesis, and lexical-hash embeddings. Discovery searches the bundled local corpus in SQLite mode; it is not live academic web search. Uploaded PDFs supply full text, while discovered local records can supply abstract-only evidence. The production PostgreSQL path uses external academic APIs. Search labels in the interface do not mean a trained dense embedding model is active: check Runtime Diagnostics.

Select the same project on every screen. Several pages start with an empty project dropdown. Navigation between pages does not consistently preserve the selection.

## 1. Sign in and inspect runtime

1. Open the app and sign in with the demo account above. Alternatively, register a separate account to demonstrate registration and isolated ownership.
2. Open Runtime Diagnostics and click Refresh Diagnostics.
3. Show database, worker, LLM provider, embedding model, and online status.
4. Explain that the provider and embedding configuration determine how outputs are produced. Do not describe local heuristic verification as an independent scientific proof.

Expected: authenticated pages load and diagnostics returns configuration without exposing API keys.

## 2. Create a research project

1. Open All Projects > New Project.
2. Project title: `RAG Factuality and Citation Evidence`.
3. Primary research question: `How can retrieval and claim-level verification improve factuality in retrieval-augmented generation?`
4. Click Create, then open the new project.
5. Show its research question, status, summary counts, and Pipeline Status panel.

Expected: a saved project appears in the list and can be reopened. Use a project with an explicit research question for the full research pipeline; automatic source-review projects may initially have only a title.

## 3. Dashboard PDF review

1. Open Dashboard and choose this project.
2. Upload `data/demo-papers/lewis_2020_rag.pdf`.
3. Set the manuscript title to the actual RAG paper title. Author and affiliation inputs are draft metadata; leave them blank or explicitly describe your review authorship rather than misattributing the original research.
4. Click Analyze paper and prepare revision once. Wait for the busy state to finish.
5. Show each detected evidence sentence and its proposed change. An imperfect sentence split or a missing gap is possible with two-column research PDFs; compare with the original.
6. Download Manuscript (.md), References (.bib), and IEEE manuscript (.tex).
7. Open the Markdown and show the original paper text and appended revision plan. Check that new experiments are not claimed.
8. Repeat for Self-RAG and FActScore in the same project if you want three full-text inputs. Each analysis creates its own source-specific draft and paper record; do not repeatedly upload a file merely to refresh the page.

Expected: source-specific findings, a saved draft, and three downloadable formats. Paper upload alone does not run every corpus synthesis stage. The gaps listed here belong to the source review; they are not automatically the same records shown by Research Gaps.

To demonstrate the no-project fix separately, use a fresh account with no projects: choose a PDF and click Analyze. The app creates a project without losing the selected file.

## 4. Literature Explorer: discovery, filtering, and comparison

1. Select the project.
2. In Academic discovery query enter `retrieval augmented generation factuality` and click Discover Papers.
3. Show the added/skipped duplicate counts. Repeat the same discovery query to demonstrate deduplication of discoverable records. Do not assume repeated manual PDF review is deduplicated in the same way.
4. Switch between Comparison Matrix and Paper Cards.
5. Filter by a title fragment such as `Self-RAG` and clear the filter.
6. Show method, dataset, metric mentions, source abstract excerpt, and limitation columns. `Not extracted` is a valid result; mentions are not necessarily measured findings.
7. Click a paper title to open its detail page. Use the Literature Explorer directly for the full list; the project detail screen currently has a View all link whose target is not registered as a route.

Expected: papers stored in this project, searchable list/card views, and source metadata where available. Manually uploaded PDFs can lack structured author/year/venue metadata.

## 5. Paper viewer and paper-specific evidence search

1. Open the uploaded RAG paper from Literature Explorer.
2. Show title, abstract, ingestion status, extracted entities, and stored claims if present.
3. Follow source/DOI links when metadata supplies them. An uploaded local paper may not have an external PDF link.
4. In the evidence Q&A form enter `What knowledge source is used for non-parametric memory?` and submit.
5. Inspect the retrieved excerpts and compare them with the original PDF. Try `RAG-Sequence RAG-Token` as a second query.

Expected: search results restricted to the selected paper. This interface retrieves evidence passages; it does not guarantee a conversational, synthesized answer. Missing metadata and extraction errors should remain visible rather than be invented.

## 6. Research Planner and complete pipeline

1. Open Research Planner and select the project.
2. Click Regenerate if a plan is absent or you want to demonstrate generating another plan.
3. Show problem definition, subquestions, inclusion/exclusion criteria, search strategy, keywords, concepts, candidate datasets, and potential experiment designs.
4. Edit the problem definition and one subquestion. These are the editable text fields currently exposed by this page.
5. Click Approve Plan & Discover. This saves the edited plan with approval and starts the discovery pipeline; the page navigates to the project.
6. Watch Pipeline Status through discovery, ingestion, analysis, extraction, synthesis, gap analysis, hypotheses, experiment design, verification, and reporting. Planning can also appear when started through Run Pipeline.
7. Wait for completed status. If failed, show the error rather than claiming completion. Active jobs disable starting another pipeline from the project page.
8. To demonstrate the other launch path, later click Run Pipeline from the project page. Re-running can add generated artifacts, so do not use it repeatedly as a refresh button.

Expected: persistent stage progress and a generated report. Exact artifact counts vary with source text and local corpus matches. Local discovery ingests abstract records without automatically fetching their remote PDFs.

## 7. Evidence Provenance

1. Select the project after the pipeline completes.
2. Show All Claims, Supported, Partially, Contradicted, and Insufficient filters.
3. Search claims using `retrieval` or another term actually visible in a claim.
4. Inspect a claim's linked evidence snippet, section, page metadata, and relevance score.
5. Compare one linked passage with the original PDF. Distinguish source wording, extracted claims, and interpretations.

Expected: evidence links where extraction and verification produced them. A status filter may have zero results. Do not invent a contradiction to populate every tab. A similarity or confidence number is not a calibrated probability that a claim is scientifically true.

## 8. Knowledge Graph

1. Select the project and open Force Graph.
2. Drag nodes, pan the graph, and zoom with the mouse wheel.
3. Click a node to show Entity Inspector, entity type, source identifier where present, and connected relations.
4. Switch to Analytics & Claims and show entity distribution, relation records, and stored claims.

Expected: graph nodes and links from stored extraction results. A sparse graph can be valid; it reflects the extracted corpus and does not establish causal relationships or exhaustive scientific knowledge.

## 9. Research Gaps

1. Select the project after the pipeline completes.
2. Read a gap title, description, type, importance field, and detected-by field.
3. Click Explore Evidence and reselect the project there if necessary. This navigation opens the general evidence screen; it does not automatically isolate the selected gap's evidence.
4. Return and click Generate Hypothesis for one gap.

Expected: hypotheses are saved and the app navigates to Hypothesis Lab. Some explanatory and score fallback text in these cards is a UI template, not a measurement extracted from the paper. Assess the gap description and actual sources.

## 10. Hypothesis Lab

1. Select the same project if needed.
2. Show statement, rationale, status, and available confidence/testability metadata.
3. Explain a hypothesis as a proposed testable statement. The displayed independent/dependent-variable and falsification panels currently contain generic templates; do not present them as generated statistical analysis.
4. Click Design Experiment Spec on one hypothesis.

Expected: a stored experiment proposal. This step does not execute the experiment or validate the hypothesis.

## 11. Experiments & Runs

1. Select the project and open the generated experiment proposal.
2. Show model specification, hyperparameters, random seed, evaluation metrics, and run history.
3. Demonstrate the alternative path: choose a hypothesis and click Generate Protocol.
4. Demonstrate manual creation with Design Experiment. Title: `DEMO ONLY - retrieval metrics recording`. Description: `Interface demonstration; no trained model or paper reproduction.` Model: `BM25 demo`. Seed: `42`. Metrics: `demo_precision, demo_recall`.
5. Save Proposal, select it, and click Record Run.
6. Replace the form's prefilled metrics with `{"demo_precision":0.6,"demo_recall":0.8}`. Clear the prefilled Git commit; enter a real commit only if it identifies actual evaluated code.
7. Click Log Run and show the stored row. Clearly call these artificial UI test values. Reload or reopen to show persistence.

Expected: the supplied values appear in run history. This is a results recorder; it does not train a model, compute metrics, reproduce RAG/Self-RAG/FActScore, or verify user-supplied measurements. The current UI can display a fallback runtime and commit label when absent; those are not evidence of measured execution. Keep demonstration results in the clearly labelled demo experiment/project.

## 12. IEEE Papers & Reports: both workflows

Corpus review:

1. Select the project and click Create corpus review after papers and pipeline artifacts exist.
2. Select the resulting report in the list.
3. Show abstract, research question, background, literature review, gaps, hypotheses, experimental design, results, limitations, conclusion, references, and unsupported-claim indicators when present.
4. Download IEEE Paper (.tex), Markdown, and BibTeX.

Source manuscript:

1. Upload a real paper PDF and click Analyze source and write draft to demonstrate the second Analyze button with real input.
2. For project-code review, use `output/pdf/verirag_demo_project.zip` or its Markdown equivalent. These are explicitly synthetic project examples, separate from the real research papers.
3. For the GitHub alternative, click Use a GitHub link instead, then enter a public repository root URL such as `https://github.com/owner/repository` using an actual small repository you intend to inspect. This path needs internet access; archives are limited to 10 MB. Uploaded code is read, not executed.
4. Inspect source-specific findings and download the draft.

Expected: source review and corpus review are separate saved reports. Exported .tex is IEEEtran source. Compile it in Overleaf with IEEEtran for a formatted PDF; this backend does not compile manuscript PDFs. Review references, attribution, and every claim before sharing a draft. A bibliography may be empty for source-only input without related stored papers.

## 13. Hybrid Search

1. Select the project.
2. Search `retrieval augmented generation Wikipedia`, then `citation factuality`, then `RAG-Sequence RAG-Token`.
3. Show result count, candidate count, search duration, reranking status, paper title, available page/section metadata, passage, and Dense/BM25/Final score fields.
4. Compare an excerpt with the PDF. Search an unrelated phrase and explain that overlap/fallback ranking can still return weak matches.

Expected: retrieval across the selected project. In the current local configuration lexical hashing is not trained semantic dense retrieval; use the displayed reranking status rather than claiming reranking necessarily ran. These scores are ranking signals, not factual accuracy percentages.

## 14. Dashboard analytics and bibliography

1. Reopen Dashboard and select the project.
2. Show corpus, claims, gaps, hypotheses, experiments, and reports counts after the workflow.
3. Show publication timeline and model/dataset mention charts. Years may be absent for manual uploads; discovered metadata can populate them. Mention counts are not model performance.
4. Open About & bibliography, search a paper title or author, and show available source links, year, venue, and authors.

Expected: the bibliography lists distinct stored papers across the signed-in user's projects. It is broader than one report's citation list. Missing metadata can appear as Authors/Year/Venue not recorded.

## 15. Persistence, project isolation, and sign out

1. Reload and confirm saved papers, drafts, and experiment run records persist.
2. Create another project, select it in Literature Explorer/Search, and show its different corpus.
3. If demonstrating deletion, create a disposable project first and delete only that project with the trash icon. The current button deletes immediately; do not click it on the main demo project.
4. Click Sign out and confirm protected pages require login. Sign back in and reopen the original project.

## Advanced API and CLI features

Open http://localhost:8001/docs to inspect routes beyond the visible UI. To call protected routes, sign in through POST /api/v1/auth/login, copy access_token, click Authorize, and paste the access token. Depending on the Swagger input label, supply the bare token rather than duplicating the Bearer prefix. Keep tokens out of screenshots.

- Projects: create/read/update/delete, research questions, and ownership checks.
- Papers: metadata import, file upload, paper detail, ingestion-related operations, discovery, and deletion; inspect the installed route schema for required fields.
- Research: generate/update plans, start stages, synthesize, list gaps, create hypotheses, and generate hypotheses for gaps.
- Jobs: list/detail/active status and cancel an active job. Use a disposable job if demonstrating cancellation.
- Retrieval: top_k, reranking request, year bounds, and metadata filters beyond the basic UI form.
- Knowledge: entity types, relation types, claim verification filters, and entity distribution.
- Experiments/reports: design proposals, record/list runs, generate reports, and export.
- Runtime/manuscripts/bibliography: runtime diagnostics, source-specific review, and corpus bibliography.

For the CLI, open PowerShell in backend and run `.venv/Scripts/python.exe -m app.cli.main --help`. It exposes create, search, analyze, gaps, hypothesis, report, and benchmark commands. Run each command with --help for exact options and supply the project ID explicitly where supported. CLI dependency/configuration requirements can differ from the running local web entrypoint; do not imply all CLI commands were exercised by the browser demo. Benchmark outputs must be inspected for real versus fixed/example scoring before presentation.

## Presentation order and troubleshooting

Recommended 20-30 minute order: login/runtime > create project > upload the real paper > literature and paper viewer > planner/pipeline > evidence > graph > gaps > hypotheses > experiment proposal and labelled demo run > reports/exports > search > dashboard/bibliography > persistence/sign out. Prepare paper uploads and pipeline output before a short presentation.

If a screen is empty, first select the project; next confirm papers are processed and the pipeline completed. Upload review findings do not automatically populate all research artifacts. If a job fails, inspect its stage and error. For PDF errors, use the supplied searchable PDFs and confirm the upload size is under 10 MB. Discovery in this SQLite demo requires bundled corpus matches, not internet. GitHub review and production API discovery require external connectivity. No new research accuracy, statistical significance, model training, or measured improvement should be inferred from a successful UI demonstration.
