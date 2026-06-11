#!/usr/bin/env python3
"""Print the research worklist across all data files.

Two kinds of entries:
- NEEDS_VERIFICATION strings anywhere in a data file (unverified facts).
- "_reviews" arrays of {path, review_by, reason}: facts that were verified but
  expire. Past-due reviews fail the run like unverified facts; reviews coming
  due within UPCOMING_DAYS are printed as notices without failing.

Run: python3 verify.py
The generator must also call needs_verification() and skip rendering any county
whose required fields are unverified."""

import datetime
import json
import sys
from pathlib import Path

DATA = Path(__file__).parent / "data"
REQUIRED_COUNTY_FIELDS = ["ami_80", "ami_120"]
UPCOMING_DAYS = 30


def walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(node, str) and "NEEDS_VERIFICATION" in node:
        yield path, node


def needs_verification(county: dict) -> bool:
    """True if any required field is still a NEEDS_VERIFICATION string."""
    return any(
        isinstance(county.get(f), str) and "NEEDS_VERIFICATION" in county[f]
        for f in REQUIRED_COUNTY_FIELDS
    )


def review_status(doc, today):
    """Split a file's _reviews into (past_due, upcoming) lists."""
    past_due, upcoming = [], []
    for r in doc.get("_reviews", []):
        due = datetime.date.fromisoformat(r["review_by"])
        if due <= today:
            past_due.append(r)
        elif (due - today).days <= UPCOMING_DAYS:
            upcoming.append(r)
    return past_due, upcoming


def main():
    today = datetime.date.today()
    total = 0
    notices = 0
    for fp in sorted(DATA.rglob("*.json")):
        if fp.name == "schema.json":
            continue
        with open(fp) as f:
            doc = json.load(f)
        rows = list(walk(doc))
        past_due, upcoming = review_status(doc, today)
        if rows or past_due or upcoming:
            print(f"\n{fp.relative_to(DATA.parent)}")
            for path, note in rows:
                print(f"  {path}: {note}")
            for r in past_due:
                print(f"  REVIEW PAST DUE {r['review_by']} {r['path']}: {r['reason']}")
            for r in upcoming:
                print(f"  review due {r['review_by']} {r['path']}: {r['reason']}")
            total += len(rows) + len(past_due)
            notices += len(upcoming)
    print(f"\n{total} fields awaiting verification or past-due review.")
    if notices:
        print(f"{notices} reviews coming due within {UPCOMING_DAYS} days.")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
