#!/usr/bin/env python3
"""Print every NEEDS_VERIFICATION field across all data files, as the research worklist.
Run: python3 verify.py
The generator must also call needs_verification() and skip rendering any county
whose required fields are unverified."""

import json
import sys
from pathlib import Path

DATA = Path(__file__).parent / "data"
REQUIRED_COUNTY_FIELDS = ["ami_80", "ami_120"]


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


def main():
    total = 0
    for fp in sorted(DATA.rglob("*.json")):
        if fp.name == "schema.json":
            continue
        with open(fp) as f:
            doc = json.load(f)
        rows = list(walk(doc))
        if rows:
            print(f"\n{fp.relative_to(DATA.parent)}")
            for path, note in rows:
                print(f"  {path}: {note}")
            total += len(rows)
    print(f"\n{total} fields awaiting verification.")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
