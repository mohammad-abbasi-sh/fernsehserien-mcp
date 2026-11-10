"""Offline tests — parse real captured fernsehserien.de pages
(scripts/styles stripped), no network."""
import json
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from fernsehserien_mcp import domain as dom
from fernsehserien_mcp import server as srv

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _read(name):
    return (FIX / name).read_text(encoding="utf-8")


class TestValidation(unittest.TestCase):
    def test_query_limit_season(self):
        self.assertEqual(dom.validate_query("  babylon "), "babylon")
        with self.assertRaises(ValueError):
            dom.validate_query("")
        self.assertEqual(dom.validate_limit(10), 10)
        with self.assertRaises(ValueError):
            dom.validate_limit(21)
        self.assertEqual(dom.validate_season(5), 5)
        with self.assertRaises(ValueError):
            dom.validate_season(0)

    def test_resolve_series(self):
        self.assertEqual(dom.resolve_series("babylon-berlin"),
                         "babylon-berlin")
        self.assertEqual(
            dom.resolve_series(
                "https://www.fernsehserien.de/babylon-berlin"),
            "babylon-berlin")
        with self.assertRaises(ValueError):
            dom.resolve_series("https://example.com/babylon-berlin")


class TestSearch(unittest.TestCase):
    def test_babylon(self):
        items = dom.parse_search_results(_read("search-babylon.html"))
        self.assertEqual(len(items), 14)
        self.assertEqual(items[3], {
            "name": "Babylon Berlin",
            "url": "https://www.fernsehserien.de/babylon-berlin",
            "info": "D 2016–2026"})
        self.assertEqual(items[0]["name"], "Babylon")
        self.assertEqual(items[0]["info"], "D 1993–2003")

    def test_nomatch(self):
        self.assertEqual(
            dom.parse_search_results(_read("search-nomatch.html")), [])


class TestDetail(unittest.TestCase):
    def test_babylon_berlin(self):
        out = dom.parse_series_detail(
            _read("series-babylon-berlin.html"), "babylon-berlin")
        self.assertEqual(out["name"], "Babylon Berlin")
        self.assertTrue(out["description"].startswith(
            "Babylon Berlin: Basierend auf den Krimi-Bestsellern"))
        self.assertEqual([s["season"] for s in out["seasons"]],
                         [1, 2, 3, 4, 5])
        self.assertEqual(out["seasons"][4]["series_id"], "32984")
        self.assertEqual(out["air_dates_url"],
                         "https://www.fernsehserien.de/babylon-berlin/sendetermine")
        self.assertEqual(dom.season_guide_url(out, 5),
                         "https://www.fernsehserien.de/babylon-berlin/episodenguide/staffel-5/32984")
        with self.assertRaises(ValueError):
            dom.season_guide_url(out, 9)


class TestEpisodes(unittest.TestCase):
    def setUp(self):
        self.eps = dom.parse_episodes(_read("episodenguide-s5.html"))

    def test_count(self):
        self.assertEqual(len(self.eps), 8)

    def test_first_episode(self):
        self.assertEqual(self.eps[0], {
            "episode_id": "1899423",
            "url": "https://www.fernsehserien.de/babylon-berlin/folgen/5x01-episode-1-1899423",
            "code": "5x01", "absolute_number": 41, "title": "Episode 1",
            "runtime_minutes": 45,
            "airings": [
                {"type": "Deutsche Streaming-Premiere",
                 "date": "Do. 10.09.2026", "channel": "ARD Mediathek"},
                {"type": "Deutsche TV-Premiere",
                 "date": "Sa. 19.09.2026", "channel": "Das Erste"}]})

    def test_all_have_code_and_airings(self):
        for e in self.eps:
            self.assertTrue(e["code"].startswith("5x"))
            self.assertGreaterEqual(len(e["airings"]), 1)


class TestAirDates(unittest.TestCase):
    def test_rows(self):
        items = dom.parse_air_dates(_read("sendetermine.html"))
        self.assertEqual(len(items), 48)
        self.assertEqual(items[0], {
            "starts": "2026-11-10T20:15:00+01:00",
            "ends": "2026-11-10T21:00:00+01:00",
            "channel": "Sky Atlantic",
            "episode_code": "2.05",
            "episode_title": "Episode 5",
            "episode_url": "https://www.fernsehserien.de/babylon-berlin/folgen/2x05-episode-5-1144172"})
        self.assertEqual(items[1]["starts"], "2026-11-10T21:00:00+01:00")


class TestServerWiring(unittest.TestCase):
    def _fetch(self, url):
        if "/suche/babylon" in url:
            return _read("search-babylon.html")
        if url.endswith("/babylon-berlin"):
            return _read("series-babylon-berlin.html")
        if "episodenguide/staffel-5" in url:
            return _read("episodenguide-s5.html")
        if url.endswith("/sendetermine"):
            return _read("sendetermine.html")
        raise AssertionError(f"unexpected URL: {url}")

    def test_search_uses_fixture(self):
        with mock.patch("fernsehserien_mcp.server._http.fetch_text",
                        side_effect=self._fetch):
            out = json.loads(srv.fs_search_series("babylon", limit=3))
        self.assertNotIn("error", out)
        self.assertEqual(out["source"], "fernsehserien.de")
        self.assertEqual(out["total_results"], 14)
        self.assertEqual(out["count"], 3)
        self.assertEqual(out["items"][0]["name"], "Babylon")

    def test_detail_uses_fixture(self):
        with mock.patch("fernsehserien_mcp.server._http.fetch_text",
                        side_effect=self._fetch):
            out = json.loads(srv.fs_series_detail("babylon-berlin"))
        self.assertEqual(out["name"], "Babylon Berlin")
        self.assertEqual(len(out["seasons"]), 5)

    def test_episodes_uses_fixtures(self):
        with mock.patch("fernsehserien_mcp.server._http.fetch_text",
                        side_effect=self._fetch):
            out = json.loads(srv.fs_episodes(
                "babylon-berlin", season=5, limit=2))
        self.assertNotIn("error", out)
        self.assertEqual(out["total_results"], 8)
        self.assertEqual(out["items"][0]["code"], "5x01")
        self.assertEqual(out["items"][0]["runtime_minutes"], 45)

    def test_episodes_bad_season(self):
        with mock.patch("fernsehserien_mcp.server._http.fetch_text",
                        side_effect=self._fetch):
            out = json.loads(srv.fs_episodes(
                "babylon-berlin", season=9))
        self.assertIn("error", out)

    def test_air_dates_uses_fixture(self):
        with mock.patch("fernsehserien_mcp.server._http.fetch_text",
                        side_effect=self._fetch):
            out = json.loads(srv.fs_air_dates("babylon-berlin", limit=2))
        self.assertEqual(out["total_results"], 48)
        self.assertEqual(out["items"][0]["channel"], "Sky Atlantic")


if __name__ == "__main__":
    unittest.main()
