# English conference paper — LaTeX source (latest two-column figure/table layout)

## Main file and class
- `main.tex`: translated paper including the citation to Huang and Zhu [8].
- `IEEEtran.cls`: the conference template class used in the earlier paper project.
- `figures/*.png`: four English-language figures corresponding to the latest column-contained Word version.

## Compile
In this folder, run:

```bash
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Or, if `latexmk` is installed:

```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

It currently builds into a 6-page US Letter PDF with placeholder author information. Adding full real author/affiliation information may change the page count.

## Before submitting
1. Replace all square-bracket author placeholders in `\\author{...}` with actual information, including affiliations and corresponding author.
2. Confirm whether the conference checklist requires `Figure 1.` / `Table 1.` or ordinary IEEE `Fig. 1` / `TABLE I`; this source follows the previously recorded conference-specific Arabic-number labels.
3. Verify reference [21] source link, because the provided Chinese manuscript listed no DOI or source URL.
4. Verify the paper against the official conference checklist and the PDF compiled on your machine.

## Layout correspondence
- Body: IEEE two-column conference layout on US Letter.
- Figures 1–4 and Tables 1–3: *inside individual columns*, never spanning both columns.
- Equations (1)–(18): one equation number each, centered mathematical display; (11), (12), (17), and (18) are each on a single line.
- Experimental numerical data and 22 references are retained from the previous English file and the latest Word revision. No experiments were rerun.

The PDF is a rendered preview, not a substitute for source files. The Word and LaTeX line breaks/page breaks need not be pixel-identical.
