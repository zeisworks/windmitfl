#!/usr/bin/env python3
"""Static site generator for windmitfl.com.

Reads data/ (the CMS), renders Jinja2 templates to output/.

Production rule (see CLAUDE.md / data/schema.json): a county page renders only
when its required fields are real values. Counties with NEEDS_VERIFICATION in
required fields are skipped and logged. `--draft` renders them anyway for
local preview, with every unverified field omitted from output and a noindex
meta tag, and excludes them from the sitemap.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from verify import needs_verification

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "output"
BASE_URL = "https://windmitfl.com"
SITE_NAME = "WindMitFL"


def fact(value):
    """Return the value, or None if it is an unverified placeholder.

    Templates must route every claim through this filter (or test) so that
    nothing flagged NEEDS_VERIFICATION ever reaches rendered output.
    """
    if isinstance(value, str) and "NEEDS_VERIFICATION" in value:
        return None
    return value


def usd(n):
    if n is None:
        return None
    return f"${n:,.0f}"


def load_json(path):
    with open(path) as f:
        return json.load(f)


def load_counties():
    counties = []
    for fp in sorted((DATA / "counties").glob("*.json")):
        c = load_json(fp)
        c["_unverified"] = needs_verification(c)
        counties.append(c)
    return counties


def load_guides():
    meta = load_json(DATA / "guides.json")
    guides = []
    for g in meta["guides"]:
        body_path = ROOT / "content" / "guides" / f"{g['slug']}.html"
        g["body"] = body_path.read_text()
        guides.append(g)
    return guides


def breadcrumb_jsonld(crumbs):
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "name": name,
                    "item": BASE_URL + url,
                }
                for i, (name, url) in enumerate(crumbs)
            ],
        }
    )


def faq_jsonld(faq):
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
                }
                for item in faq
            ],
        }
    )


class Site:
    def __init__(self, draft):
        self.draft = draft
        self.statewide = load_json(DATA / "statewide.json")
        self.counties = load_counties()
        self.guides = load_guides()
        self.sitemap_urls = []
        self.env = Environment(
            loader=FileSystemLoader(ROOT / "templates"),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters["fact"] = fact
        self.env.filters["usd"] = usd
        self.env.globals.update(
            site_name=SITE_NAME,
            base_url=BASE_URL,
            statewide=self.statewide,
        )

    def render(self, template, url, *, crumbs, noindex=False, **ctx):
        """Render template to output/<url>/index.html (or literal file path)."""
        page = {
            "url": url,
            "canonical": BASE_URL + url,
            "noindex": noindex,
            "breadcrumb_jsonld": breadcrumb_jsonld(crumbs),
            "crumbs": crumbs,
        }
        html = self.env.get_template(template).render(page=page, **ctx)
        if url.endswith("/"):
            dest = OUT / url.lstrip("/") / "index.html"
        else:
            dest = OUT / url.lstrip("/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html)
        if not noindex:
            self.sitemap_urls.append(url)

    def build(self):
        if OUT.exists():
            shutil.rmtree(OUT)
        OUT.mkdir()
        shutil.copytree(ROOT / "static", OUT / "static")

        published, skipped = [], []
        for c in self.counties:
            if c["_unverified"] and not self.draft:
                skipped.append(c["slug"])
            else:
                published.append(c)

        # Home
        self.render(
            "home.html",
            "/",
            crumbs=[("Home", "/")],
            counties=[c for c in published if not c["_unverified"]],
            guides=self.guides,
        )

        # County hubs
        for c in published:
            url = f"/county/{c['slug']}/"
            self.render(
                "county.html",
                url,
                crumbs=[("Home", "/"), (c["name"], url)],
                noindex=c["_unverified"],
                county=c,
                faq_jsonld=faq_jsonld(c["faq"]),
            )

        # Guides
        self.render(
            "guides_index.html",
            "/guides/",
            crumbs=[("Home", "/"), ("Guides", "/guides/")],
            guides=self.guides,
        )
        for g in self.guides:
            url = f"/guides/{g['slug']}/"
            self.render(
                "guide.html",
                url,
                crumbs=[("Home", "/"), ("Guides", "/guides/"), (g["title"], url)],
                guide=g,
            )

        # Tools
        self.render(
            "tool_eligibility.html",
            "/tools/msfh-eligibility/",
            crumbs=[("Home", "/"), ("MSFH Eligibility Checker", "/tools/msfh-eligibility/")],
        )
        self.render(
            "tool_estimator.html",
            "/tools/savings-estimator/",
            crumbs=[("Home", "/"), ("Savings Estimator", "/tools/savings-estimator/")],
        )

        # Legal (drafts pending review; indexable once approved, noindex for now)
        for slug, tpl, title in (
            ("privacy", "privacy.html", "Privacy Policy"),
            ("terms", "terms.html", "Terms of Use"),
        ):
            self.render(
                tpl,
                f"/{slug}/",
                crumbs=[("Home", "/"), (title, f"/{slug}/")],
                noindex=True,
            )

        self.write_sitemap()
        self.write_robots()

        print(f"Built {len(self.sitemap_urls)} indexable pages to {OUT}/")
        if self.draft:
            drafts = [c["slug"] for c in published if c["_unverified"]]
            if drafts:
                print(f"DRAFT (noindex, unverified fields omitted): {', '.join(drafts)}")
        for slug in skipped:
            print(
                f"SKIPPED county/{slug}: required fields unverified. "
                f"Run `make verify` for the worklist."
            )

    def write_sitemap(self):
        rows = "\n".join(
            f"  <url><loc>{BASE_URL}{u}</loc></url>" for u in self.sitemap_urls
        )
        (OUT / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{rows}\n</urlset>\n"
        )

    def write_robots(self):
        (OUT / "robots.txt").write_text(
            f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--draft",
        action="store_true",
        help="render counties with unverified required fields (noindex)",
    )
    args = parser.parse_args()
    Site(draft=args.draft).build()
    return 0


if __name__ == "__main__":
    sys.exit(main())
