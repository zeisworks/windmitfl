# windmitfl.com — Build Spec

Florida wind mitigation navigator site. Programmatic SEO + lead gen. This file is the
source of truth for architecture, design, data, and monetization. Do not invent facts:
every claim on the site must come from `data/statewide.json`, `data/counties/*.json`,
or a cited primary source. Fields marked `NEEDS_VERIFICATION` must be verified against
the listed source before publishing, or omitted from rendered output.

## What this site is

The independent navigator for Florida's wind mitigation money: the new OIR-B1-1802
inspection form, insurance discounts, and the My Safe Florida Home (MSFH) grant
program, broken down by county. Every competitor ranking today is a contractor or
inspector selling their own service. This site is neutral and comprehensive. That
neutrality is the brand, the link-earning strategy, and the conversion trust signal.

Positioning rules:
- Never read like a contractor site. No "call us today." No first-person plural sales voice.
- Explain how the system works and show the numbers. Never tell a specific homeowner
  what insurance to buy. Never guarantee savings. Include a not-an-adviser disclaimer
  component on every money-related page.
- Every page shows a "Last verified" date sourced from the data file's `last_verified` field.

## Stack

- Static site generation. Python 3.12 + Jinja2 (both available). No framework lock-in
  needed; plain SSG from JSON data files is correct for this. If you prefer Astro,
  that is acceptable, but do not add a CMS or database. JSON files in `data/` are the CMS.
- Output: static HTML to `output/`, deployable to any static host.
- One shared CSS file built from the design tokens below. No Tailwind, no CSS framework.
- Tools (eligibility checker, savings estimator) are self-contained vanilla JS embedded
  on their pages. No build step for JS.

## Architecture / page types

URL structure:
- `/` home
- `/county/{slug}/` 67 county hubs (launch the 15 in `data/launch_counties.txt` first)
- `/county/{slug}/{city-slug}/` city pages, only where `cities[]` exists in county data
- `/guides/{slug}/` evergreen guides (list in section below)
- `/tools/msfh-eligibility/` eligibility checker
- `/tools/savings-estimator/` discount estimator
- `/inspectors/{county-slug}/` inspector directory pages (Phase 2, after DBPR scrape)

Every page: unique title/meta description from data, BreadcrumbList JSON-LD,
FAQPage JSON-LD where FAQ blocks exist, canonical tags, XML sitemap, robots.txt.

### County hub template sections (in order)

1. Advisory header (signature element, see design): county name, risk designation,
   "Last verified" date.
2. Data strip: 4 key figures from county JSON (avg premium context, windstorm share,
   AMI thresholds, inspection cost range).
3. "What changed under the 2026 form" module (statewide content, county-aware intro).
4. MSFH eligibility for this county: income tier table computed from `ami_80` / `ami_120`,
   priority group explainer, program status pulled from `statewide.json.msfh.status`.
5. Insurance savings context: windstorm-portion explanation, feature credit summary.
6. Inspector directory block (Phase 2; render a "find a licensed inspector" DBPR
   link until directory data exists).
7. FAQ (6-8 questions, county-localized wording, FAQPage schema).
8. CTA blocks per monetization section below.

### Evergreen guides (write these 10 first, in this order)

1. The 2026 wind mitigation form explained (OIR-B1-1802 rev. 04/26): what changed
2. My Safe Florida Home application walkthrough (current cycle)
3. The MSFH backlog: why ~45,000 homeowners are waiting and what the 2026-27 budget does
4. Wind mitigation inspection cost and what happens during one
5. Feature guide: roof shape (hip vs gable) credits
6. Feature guide: roof-to-wall attachment (clips vs straps)
7. Feature guide: roof deck attachment and ring-shank nails
8. Feature guide: secondary water resistance
9. Feature guide: opening protection and the all-or-nothing rule
10. My wind mit report expired / is older than the new form: what to do

Guide content rules: 1,200-2,000 words, prose-first, no bullet spam, every factual
claim traceable to `statewide.json` or a cited primary source (OIR, FL DFS,
mysafeflhome.com, Florida Statutes 627.0629 / 627.711). Cite primary sources inline
as links. Do not cite contractor blogs.

## Design tokens (locked — do not substitute defaults)

Aesthetic direction: Florida civic/advisory. The visual vernacular is the NWS weather
advisory and the state inspection form, not a SaaS landing page and not the
cream-paper/terracotta look.

Palette:
- `--ink: #16242E` (storm slate, body text and footer bg)
- `--paper: #FAFAF7` (page background)
- `--surf: #0F6E7C` (gulf teal, links, section accents)
- `--cone: #D9560B` (hurricane-cone orange, CTAs and advisory bar ONLY, use sparingly)
- `--sand: #E9E4D8` (data strip and table backgrounds)
- `--line: #C9CFCB` (hairlines)

Type:
- Display: Archivo (700/900, tight tracking) — headlines, data figures
- Body: Public Sans (400/600) — the USWDS face; government-form vernacular is the point
- Utility: IBM Plex Mono (500) — eyebrows, data labels, "Last verified" stamps
- Load via Google Fonts with `font-display: swap`.

Signature element: the advisory bar. A full-width strip at the top of county pages
styled like a weather-service advisory: mono uppercase eyebrow
(`COUNTY ADVISORY / {COUNTY} / UPDATED {DATE}`), county name in Archivo 900 below.
Section headers across the site use form-document eyebrows in Plex Mono:
`SEC. 02 / MSFH ELIGIBILITY`. These two devices carry the identity; everything else
stays quiet. No gradients, no glassmorphism, no decorative animation. Border-radius 2px max.

Quality floor: responsive to 360px, visible keyboard focus, WCAG AA contrast,
`prefers-reduced-motion` respected, semantic HTML.

## Monetization wiring

1. Profitise home insurance lead form. Embed code TBD by Jack (he has the publisher
   account). Build a `<section class="cta-insurance">` component with a placeholder
   `<!-- PROFITISE_EMBED -->` comment where the form snippet drops in. Placement:
   after section 5 on county pages, end of insurance-related guides. Copy frame:
   "Your windstorm premium is the part discounts apply to. If your carrier won't
   apply them, compare." Neutral voice, no hard sell.
2. Inspector directory placements (Phase 2): featured listing slots per county.
   Build the directory template with `featured: true` support in inspector records.
3. Contractor leads (Phase 3): per-county quote-request form for opening
   protection / roof work. Build the form component now, route to a placeholder
   endpoint; Jack wires routing later.
4. Compliance: every lead form includes explicit TCPA-style consent language
   (checkbox, not pre-checked) and a privacy policy link. Build `/privacy/` and
   `/terms/` pages from standard static templates and flag them for legal review.

## Data layer

See `data/schema.json` for the county schema and `data/statewide.json` for shared
facts including the MSFH program status changelog. Three seed counties are provided
(Miami-Dade, Hillsborough, Pinellas) with verified statewide facts filled in and
county-specific figures marked `NEEDS_VERIFICATION` with their source listed.

Maintenance contract (build this into the workflow, it is the product):
- `statewide.json.msfh.changelog[]` gets a dated entry whenever program status
  changes. The county pages render the latest entry in the MSFH section.
- A `make verify` task should print every field across all data files still marked
  NEEDS_VERIFICATION, with its source URL, as the research worklist.

## Build order

1. Generator + base templates + design system, rendering the 3 seed counties and
   guide #1 end to end.
2. Guides 1-10.
3. Eligibility checker tool (logic spec in `data/statewide.json.msfh.eligibility`).
4. Remaining launch counties (data files to be added as research completes).
5. Savings estimator, city pages, inspector directory.

## What NOT to do

- Do not generate county or city pages whose data files are mostly placeholders.
  Thin pages are worse than absent pages.
- Do not invent premium figures, AMI numbers, or program dates. Render nothing
  rather than render a guess.
- Do not add testimonials, fake review counts, or urgency banners.
- Do not use em dashes anywhere in site copy.
