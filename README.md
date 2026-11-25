# 607 Journalists

A static, searchable web edition of Joseph R. B. Sutherland’s April 2015 dissertation.

Open `dist/index.html` directly in a browser. No installation or server is required. Search, chapter links, and original page images work offline.

The complete original PDF is included. Text was extracted with macOS PDFKit; paragraph boundaries were reconstructed from line positions. Original page images preserve diagrams, tables, and complex layouts alongside the reflowed text. Historical wording and references are retained.

To regenerate the HTML and search index: `python3 build.py`. The stylesheet and browser script are maintained directly in `dist/`.

Validation: JavaScript syntax, all internal anchors, local asset references, and presence of all 73 content pages were checked. Browser visual QA was unavailable.

Hosting: Site identity is saved in `.openai/hosting.json`. Publication did not complete because the environment could not resolve `git.chatgpt-team.site`. Reuse the saved project ID when resuming publication.

## Figures and citations

All 20 figures now have individual anchors and captions. Figures 3, 4 and 7 are accessible HTML reconstructions; figures 8–15, 17 and 18 use the original PDF vector geometry; figures 16, 19 and 20 are regenerated from published values with accessible data tables. The two pie charts are presented as horizontal bars. Figures 1, 2, 5 and 6 retain cropped source graphics; source data for the latter two graphs are not supplied. Every figure links back to its PDF page.

The 165 bibliography entries have stable anchors. There are 204 explicit author/year citation links and return links to their calling passages. Editorial citation corrections are documented in the bibliography notes: the Singh bibliography year is corrected to 2008, and the Kittur citation in section 2.5 is clarified as 2007a. `citation-audit.json` records matching results. Context-dependent “ibid.” remains unchanged.

Run `python3 build.py` and `python3 validate.py`. `figures.py`, `pdf_vectors.py`, and `references.py` contain the reconstruction and matching logic. `typography.py` italicises “et al.” in visible web text while preserving HTML attributes and source data. The PDF vector converter is specific to this source document, not a general-purpose PDF conversion library. Cropped source graphics are retained in `dist/assets/figures/`.

Validation for this revision: internal links, unique IDs, local assets, SVG XML, chart totals and calculations passed. Recreated charts were rendered and visually inspected with the available local WebKit renderer. Full modern-browser interaction testing remains unavailable. Hosting still requires access to the Sites Git server.

## Continuous reading

The web edition flows continuously without PDF page dividers, page labels, or inline page scans. Chapter navigation, figures, citations, and existing deep links remain available. Search labels matching passages by chapter. Download the PDF for original page layouts.

## Registered users

Appendix 8.2 preserves all 436 usernames in PDF column order, with linked user pages. Symbols reproduce the historical role markings: † administrator, ‡ user with rollback, § subsequently blocked user. `user_roles.py` recovers these from the original PDF fonts and underline strokes; these are the dissertation’s classifications, not current account statuses. Validation checks all markers against the extracted roles.

## Typography and styling

Newsreader is used for titles and reading text, paired with Manrope for navigation and labels. Google Fonts supplies the web fonts when online; Georgia and system fonts keep the complete edition readable offline. The stylesheet uses a cool white background, blue links and controls, and coral red accents drawn from the graphics, responsive reading widths, keyboard focus styling, and print rules.
