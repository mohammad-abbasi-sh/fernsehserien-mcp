"""Live tests — hit the real fernsehserien.de. Cautious: few requests.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set FERNSEHSERIEN_SKIP_LIVE=1)
"""
import json
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from fernsehserien_mcp import server as srv

pytestmark = pytest.mark.live
SKIP = os.environ.get("FERNSEHSERIEN_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="FERNSEHSERIEN_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_search_live(self):
        out = json.loads(srv.fs_search_series("babylon", limit=10))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["total_results"], 5)
        slugs = [i["url"].rsplit("/", 1)[-1] for i in out["items"]]
        self.assertIn("babylon-berlin", slugs)
        print(f"\nLIVE search babylon: {out['total_results']} series — "
              f"top: {out['items'][0]['name']}")

    def test_detail_live(self):
        out = json.loads(srv.fs_series_detail("babylon-berlin"))
        self.assertNotIn("error", out)
        self.assertEqual(out["name"], "Babylon Berlin")
        self.assertGreaterEqual(len(out["seasons"]), 5)
        print(f"\nLIVE detail Babylon Berlin: "
              f"{len(out['seasons'])} seasons")

    def test_episodes_live(self):
        out = json.loads(srv.fs_episodes(
            "babylon-berlin", season=5, limit=2))
        self.assertNotIn("error", out)
        self.assertEqual(out["total_results"], 8)
        self.assertEqual(out["items"][0]["code"], "5x01")
        print(f"\nLIVE episodes S5: {out['total_results']} episodes — "
              f"first: {out['items'][0]['title']}, "
              f"{out['items'][0]['runtime_minutes']} min")

    def test_air_dates_live(self):
        out = json.loads(srv.fs_air_dates("babylon-berlin", limit=2))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["total_results"], 1)
        print(f"\nLIVE air dates: {out['total_results']} rows — "
              f"next: {out['items'][0]['starts']} "
              f"{out['items'][0]['channel']} "
              f"{out['items'][0]['episode_code']}")

    def test_nomatch_live(self):
        out = json.loads(srv.fs_search_series("xyzqweabc"))
        self.assertNotIn("error", out)
        self.assertEqual(out["total_results"], 0)
