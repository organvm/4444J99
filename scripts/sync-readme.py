#!/usr/bin/env python3
"""
sync-readme — inject the single-source ecosystem stats into README.md markers.

Reads data/ecosystem.yml and replaces the content between each
`<!-- v:KEY -->...<!-- /v -->` pair in README.md with the matching value.

Usage:
  python3 scripts/sync-readme.py            # rewrite README.md in place
  python3 scripts/sync-readme.py --check    # exit 1 if README is out of sync

Environment overrides:
  ECOSYSTEM_DATA  — path to the data file (default: data/ecosystem.yml)
  README_PATH     — path to the README   (default: README.md)
"""

import argparse
import os
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKER = re.compile(r"(<!-- v:([A-Za-z0-9_]+) -->)(.*?)(<!-- /v -->)")


def render(readme_text: str, data: dict) -> tuple[str, list[str]]:
    """Return (new_text, warnings). Replaces each marker's body with data[KEY]."""
    warnings: list[str] = []
    seen_keys: set[str] = set()

    def repl(m: re.Match) -> str:
        key = m.group(2)
        seen_keys.add(key)
        if key not in data:
            warnings.append(f"marker '{key}' has no entry in the data file")
            return m.group(0)
        return f"{m.group(1)}{data[key]}{m.group(4)}"

    new_text = MARKER.sub(repl, readme_text)
    for key in data:
        if key not in seen_keys:
            warnings.append(f"data key '{key}' has no matching marker in the README")
    return new_text, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="verify README is in sync; exit 1 on drift (no write)")
    args = parser.parse_args()

    data_path = Path(os.environ.get("ECOSYSTEM_DATA") or REPO_ROOT / "data/ecosystem.yml")
    readme_path = Path(os.environ.get("README_PATH") or REPO_ROOT / "README.md")

    raw = yaml.safe_load(data_path.read_text()) or {}
    data = {k: ("" if v is None else str(v)) for k, v in raw.items()}

    original = readme_path.read_text()
    new_text, warnings = render(original, data)
    for w in warnings:
        print(f"warn: {w}", file=sys.stderr)

    if args.check:
        if new_text != original:
            print("error: README.md is out of sync with data/ecosystem.yml — "
                  "run `python3 scripts/sync-readme.py`", file=sys.stderr)
            return 1
        print("README.md is in sync.")
        return 0

    if new_text != original:
        readme_path.write_text(new_text)
        print(f"updated {readme_path.relative_to(REPO_ROOT)}")
    else:
        print("README.md already in sync — no change.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
