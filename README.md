# windmitfl.com

Static site for the independent Florida wind mitigation navigator. The full
spec (architecture, design tokens, data rules, monetization) lives in
[CLAUDE.md](CLAUDE.md). JSON files in `data/` are the CMS.

## Commands

```
make build    # production build to output/ (skips counties with unverified required fields)
make draft    # also renders unverified counties, noindexed, unverified figures omitted
make verify   # research worklist: NEEDS_VERIFICATION fields plus past-due and upcoming dated reviews (_reviews in data files)
make serve    # serve output/ at http://localhost:8000
```

Requires Python 3.11+ and Jinja2 (`pip install jinja2`).

## Deploying (Cloudflare Workers)

`wrangler.jsonc` serves the generated `output/` directory as static assets
(404s fall through to the built 404 page). Because `output/` is gitignored,
the Workers Builds project must generate it before deploying:

- Build command: `pip install jinja2 && make build`
- Deploy command: `npx wrangler deploy`
- Branch: `main`

## Layout

- `build.py` generator; `verify.py` verification worklist
- `data/statewide.json` shared verified facts and the MSFH changelog
- `data/counties/*.json` one file per county (`data/schema.json` is the schema)
- `content/guides/*.html` guide bodies; metadata in `data/guides.json`
- `templates/`, `static/` Jinja2 templates and the design system CSS

## Publishing workflow

1. `make verify` to see what still needs research.
2. Replace `NEEDS_VERIFICATION` strings in data files with verified values
   (update `last_verified` and, for MSFH status changes, append to
   `statewide.json.msfh.changelog`).
3. `make build`: counties publish automatically once their required fields
   (`ami_80`, `ami_120`) hold real values.
4. Verified facts that expire carry a dated entry in a data file's `_reviews`
   array; `make verify` fails on past-due reviews and lists ones coming due
   within 30 days. The big cluster is 2026-07-01 (budget signature, tax
   package, the s. 215.5586 subparagraph 7 sunset).

## Blocked on Jack

- Profitise publisher embed snippet: replaces `<!-- PROFITISE_EMBED -->` in
  `templates/partials/cta_insurance.html`.
- Contractor quote form routing: `templates/partials/contractor_form.html`
  posts to a placeholder endpoint.
- Legal review of `/privacy/`, `/terms/`, and the TCPA-style consent copy in
  the contractor form (all currently noindexed / draft-flagged).
