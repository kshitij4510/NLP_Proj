# Manuscript and paper revision workflow

Source review version 2 preserves complete PDF text blocks with physical page numbers, separates author-stated future work from limitation candidates, and reports evaluation/reproducibility/ablation mentions in a separate documentation checklist. Missing keyword matches require manual review; they are not claims that the paper omitted documentation or experiments. Existing saved drafts retain their original findings; analyze the source again for an updated draft.

Analyze creates a project automatically from the manuscript title or source filename when no project is selected. Both screens preserve the chosen file while creating the project. Manuscripts selects the first available project by default. See [the demo walkthrough](demo-walkthrough.md) for sample PDF, Markdown, and ZIP inputs and a presentation checklist.

Open Dashboard, select a project, and upload a searchable PDF to review source limitations and documentation gaps. The result shows source evidence and proposed changes and offers IEEEtran LaTeX, Markdown, and BibTeX downloads. The original paper content is preserved in the revision draft. No claimed performance improvements are fabricated.

Open Manuscripts to upload a project ZIP, documentation, source file, or PDF, or supply https://github.com/owner/repository. Only public repositories can be fetched; upload a ZIP for private repositories. Files are inspected without executing code. Sources are limited to 10 MB; archives exclude dependency directories and .env files. Provide a manuscript title if desired.

In local demo mode, output is an extractive source-based draft with revision proposals. A configured supported LLM provider synthesizes manuscript sections from inspected source and findings. The backend does not execute experiments, implement proposed code changes, or compile PDFs. Compile IEEE LaTeX in Overleaf with IEEEtran, enter authors and affiliations, and review all claims before submission.

BibTeX exports use stored citation metadata with conference entry types and escaping. Related corpus sources are selected by title overlap and require relevance review. A project with no uploaded paper or matching literature has an explicitly empty bibliography. Markdown and IEEE exports contain the same report sections. Older corpus reviews remain available separately from source-specific drafts.

About & bibliography lists every distinct paper stored across the signed-in user's projects, including uploaded papers, with authors, venue, year, and source links where known. This corpus list is separate from the sources cited in each manuscript.
