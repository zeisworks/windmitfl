# windmitfl.com

Static site for the independent Florida wind mitigation navigator. The full
spec (architecture, design tokens, data rules, monetization) lives in
[CLAUDE.md](CLAUDE.md). JSON files in `data/` are the CMS.

## Commands

```
make build    # production build to output/ (skips counties with unverified required fields)
make draft    # also renders unverified counties, noindexed, unverified figures omitted
make verify   # prints every NEEDS_VERIFICATION field with its source: the research worklist
make serve    # serve output/ at http://localhost:8000
```

Requires Python 3.11+ and Jinja2 (`pip install jinja2`).

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
