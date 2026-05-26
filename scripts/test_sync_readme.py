#!/usr/bin/env python3
"""Tests for scripts/sync-readme.py marker rendering.

Run:  python3 scripts/test_sync_readme.py
"""

import importlib.util
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("sync_readme", _HERE / "sync-readme.py")
sr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sr)


class RenderTests(unittest.TestCase):
    def test_replaces_marker_body(self):
        text = "x <!-- v:total_repos -->1<!-- /v --> y"
        out, warns = sr.render(text, {"total_repos": "148"})
        self.assertEqual(out, "x <!-- v:total_repos -->148<!-- /v --> y")
        self.assertEqual(warns, [])

    def test_multiple_markers_one_line(self):
        text = ("<!-- v:total_repos -->0<!-- /v --> / "
                "<!-- v:total_organs -->0<!-- /v -->")
        out, _ = sr.render(text, {"total_repos": "148", "total_organs": "10"})
        self.assertIn("<!-- v:total_repos -->148<!-- /v -->", out)
        self.assertIn("<!-- v:total_organs -->10<!-- /v -->", out)

    def test_marker_without_data_is_left_and_warned(self):
        text = "<!-- v:unknown -->keep<!-- /v -->"
        out, warns = sr.render(text, {})
        self.assertEqual(out, text)
        self.assertTrue(any("unknown" in w for w in warns))

    def test_data_without_marker_warns(self):
        out, warns = sr.render("no markers here", {"orphan": "1"})
        self.assertEqual(out, "no markers here")
        self.assertTrue(any("orphan" in w for w in warns))

    def test_idempotent(self):
        text = "<!-- v:total_repos -->148<!-- /v -->"
        once, _ = sr.render(text, {"total_repos": "148"})
        twice, _ = sr.render(once, {"total_repos": "148"})
        self.assertEqual(once, twice)

    def test_real_readme_in_sync_with_data(self):
        """The committed README must already match the committed data file."""
        data_raw = sr.yaml.safe_load((sr.REPO_ROOT / "data/ecosystem.yml").read_text())
        data = {k: str(v) for k, v in data_raw.items()}
        readme = (sr.REPO_ROOT / "README.md").read_text()
        out, _ = sr.render(readme, data)
        self.assertEqual(out, readme, "README.md is out of sync with data/ecosystem.yml")


if __name__ == "__main__":
    unittest.main()
