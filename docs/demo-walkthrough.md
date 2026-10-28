# ResearchMind demonstration kit

For real published papers and every feature, see [Complete feature demonstration](complete-feature-demo.md). Original searchable PDFs are in `data/demo-papers/`.

## Start locally (Windows PowerShell, from the repository root)

Install backend dependencies once into `backend/.venv`, using
`backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-local.txt`.
If the environment does not exist, first run `python -m venv backend/.venv`.
Run `cd backend` then `.venv/Scripts/python.exe local_main.py`.
In another terminal run `cd frontend`, `npm ci`, then `npm run dev`.
Open the address printed by Vite. Register or sign in with your own account.
Local mode uses SQLite and demo synthesis without an API key.

## Five-minute demonstration

1. Open Dashboard. Choose `output/pdf/verirag_demo_paper.pdf`. Optionally enter a title, authors, and affiliation. Click **Analyze paper and prepare revision**. With no selected project, Analyze creates a project automatically. Wait for the draft or a visible error; do not repeatedly click.
2. Show the evidence sentences about multilingual queries and contradictory evidence. Explain that proposed changes have not been implemented or experimentally validated. The source deliberately omits ablation and reproducibility documentation.
3. Download Markdown, IEEE `.tex`, and BibTeX `.bib`. Open Markdown to show the preserved source and revision proposals. Compile `.tex` in Overleaf with IEEEtran for a formatted manuscript PDF; the app itself exports source, not a compiled PDF.
4. Open **IEEE Papers & Reports**. Select the same project if needed. Upload `verirag_demo_project.zip` and click **Analyze source and write draft**. The ZIP contains a README and illustrative Python source; uploaded code is inspected, not executed. Use `verirag_demo_project.md` for a simpler alternative.
5. Show the saved draft in the report list and **About & bibliography** for the uploaded paper. A source-code-only project with no relevant corpus records may correctly export an empty bibliography.

## Additional checks

- In a fresh account with no projects, upload the PDF and analyze: project creation and analysis should work without navigating away or losing the file.
- With an existing project, analyze a second source and confirm its exports contain that source.
- In Manuscripts, use **Use a GitHub link instead** to enable URL entry after choosing a file. Public repository review requires internet access and an archive smaller than 10 MB; ZIP is the offline demo option.
- A blank/scanned PDF without searchable text should produce a readable validation error, not a draft. OCR is not supplied by this workflow.
- No file and no repository URL keeps Analyze disabled. Invalid GitHub URLs and unsupported uploads should return visible validation errors.
- Use Literature Explorer to add corpus records before demonstrating broader corpus features. Run the project pipeline from its project page, then inspect claims, gaps, hypotheses, graph, and reports. SQLite discovery uses the bundled local corpus; production PostgreSQL discovery uses external academic APIs. This kit alone does not create real experimental measurements.

The paper, authors, project, and study are fictional demonstration material. Do not present them as published work or measured evidence. Regenerate the kit with `python scripts/create_demo_kit.py` (requires ReportLab).
