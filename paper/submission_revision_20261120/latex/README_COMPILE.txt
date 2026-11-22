English conference manuscript revised 20 November 2026

Files
  main.tex and IEEEtran.cls: revised editable LaTeX manuscript and retained class.
  main.pdf: compiled 8-page preview with author placeholders.
  Network_Defense_Revised.docx: synchronized editable Word manuscript, 7 pages in Word.
  figures/: vector PDF/SVG figures and 600-dpi PNG versions for Word.
  data/: frozen controls, saved states, original diagnostic records and environment.
  scripts/rebuild_figures.py: redraws the figures from the included saved data.

Compile
  Recommended with Times New Roman installed:
    xelatex -interaction=nonstopmode main.tex
    xelatex -interaction=nonstopmode main.tex
  Tectonic is also supported:
    tectonic main.tex
  pdfLaTeX uses Times-compatible newtx text and math fonts:
    pdflatex -interaction=nonstopmode main.tex
    pdflatex -interaction=nonstopmode main.tex
  Packages include newtxmath, cite, booktabs, tabularx, microtype and hyperref.
  No shell escape is needed.

Author information
  Replace the bracketed author, affiliation, location and email placeholders manually.
  The corresponding author is marked with an asterisk.
  After filling the author block, recompile and check pagination. The optional
  IEEEtriggeratref{19} balances the current final bibliography page; adjust or remove
  that line if the final author block changes reference pagination.

Rebuild figures
  Requires Python 3.11+, NumPy, Matplotlib, and Times New Roman installed.
    python scripts/rebuild_figures.py
  This redraws all four figures and checks comparable panel alignment.
  It does not re-optimize controls or rerun research experiments.
  The delivered figures additionally passed rendered-PDF text-size and collision
  checks, plus the complete manuscript was visually reviewed.

Remaining verification items
  1. Authors and affiliations are intentionally left for the author to complete.
  2. Reference [13] retains the supplied author list because its full official
     article metadata could not be recovered. Its journal name is corrected to
     Netinfo Security; no author or DOI was invented.
  3. Word retains native, editable Office equations. Its built-in mathematical
     glyphs still use Cambria Math. The older Word template requests Times New
     Roman/Symbol, while the checklist requires editable Office/MathType equations.
     Exact Word math-font compliance is therefore not claimed. If the organizer
     requires the older font restriction literally, confirmation or a MathType
     conversion is still needed. Equations were not flattened into pictures.

Reproducibility scope
  All 18 numbered model/equilibrium/action/deviation equations are unchanged.
  Model parameters, final controls, plotted trajectory samples and comparison
  values are unchanged. Additional diagnostic figures in the text are taken from
  existing archived runs. The package includes saved outputs for checking and
  redrawing; it is not a new standalone optimizer implementation.
