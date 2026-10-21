"""Offline tests. The fetch layer is replaced by a dict of saved fixtures."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import aeo_check as a  # noqa: E402

BASE = "https://bakery.example"


def fx(name: str) -> str:
    return (HERE / "fixtures" / name).read_text()


def make_fetch(files: dict, calls: list | None = None):
    """files maps URL to (status, body). Anything else is a 404."""
    def fetch(url):
        if calls is not None:
            calls.append(url)
        status, body = files.get(url, (404, ""))
        return a.Response(url, status, {}, body, "" if status < 400 else f"HTTP {status}")
    return fetch


def by_id(result):
    return {c["id"]: c for c in result["checks"]}


GOOD = {
    BASE + "/": (200, fx("good.html")),
    BASE + "/robots.txt": (200, fx("robots_open.txt")),
    BASE + "/llms.txt": (200, fx("llms_good.txt")),
    BASE + "/sitemap.xml": (200, fx("sitemap.xml")),
}


class RobotsTests(unittest.TestCase):
    def test_exact_group_beats_star(self):
        groups, _ = a.parse_robots(fx("robots_open.txt"))
        self.assertEqual(a.robots_verdict(groups, "GPTBot", "/admin/x"), (True, "gptbot"))
        self.assertEqual(a.robots_verdict(groups, "ClaudeBot", "/admin/x"), (False, "*"))

    def test_grouped_agents_share_rules(self):
        groups, _ = a.parse_robots(fx("robots_blocked.txt"))
        self.assertFalse(a.robots_verdict(groups, "GPTBot")[0])
        self.assertFalse(a.robots_verdict(groups, "CCBot")[0])

    def test_partial_disallow_does_not_block_root(self):
        groups, _ = a.parse_robots(fx("robots_blocked.txt"))
        self.assertTrue(a.robots_verdict(groups, "ClaudeBot", "/")[0])
        self.assertFalse(a.robots_verdict(groups, "ClaudeBot", "/private/x")[0])

    def test_longest_match_wins(self):
        groups, _ = a.parse_robots(fx("robots_blocked.txt"))
        self.assertFalse(a.robots_verdict(groups, "Claude-User", "/")[0])
        self.assertTrue(a.robots_verdict(groups, "Claude-User", "/public/page")[0])

    def test_wildcard_and_end_anchor(self):
        groups, _ = a.parse_robots("User-agent: *\nDisallow: /*.pdf$\n")
        self.assertFalse(a.robots_verdict(groups, "GPTBot", "/a/b.pdf")[0])
        self.assertTrue(a.robots_verdict(groups, "GPTBot", "/a/b.pdf?x=1")[0])

    def test_empty_disallow_allows_all(self):
        groups, _ = a.parse_robots("User-agent: *\nDisallow:\n")
        self.assertTrue(a.robots_verdict(groups, "GPTBot", "/x")[0])

    def test_sitemap_lines(self):
        _, sitemaps = a.parse_robots(fx("robots_open.txt"))
        self.assertEqual(sitemaps, [BASE + "/sitemap.xml"])


class RunTests(unittest.TestCase):
    def test_good_site_has_no_fail_or_warn(self):
        r = a.run(BASE + "/", fetch=make_fetch(GOOD))
        self.assertEqual(r["counts"], {"pass": 12, "warn": 0, "fail": 0}, r["checks"])
        self.assertEqual(len(r["crawlers"]), len(a.CRAWLERS))

    def test_script_text_not_counted_as_words(self):
        p = a.parse_html(fx("good.html"))
        self.assertGreaterEqual(p.words, 300)
        self.assertLess(p.words, 400)

    def test_blocked_answer_crawlers_fail(self):
        files = dict(GOOD, **{BASE + "/robots.txt": (200, fx("robots_blocked.txt"))})
        c = by_id(a.run(BASE + "/", fetch=make_fetch(files)))
        self.assertEqual(c["crawlers-answer"]["status"], "fail")
        self.assertIn("PerplexityBot", c["crawlers-answer"]["summary"])
        self.assertIn("Claude-User", c["crawlers-answer"]["summary"])
        self.assertEqual(c["crawlers-training"]["status"], "warn")

    def test_star_block_fails(self):
        files = dict(GOOD, **{BASE + "/robots.txt": (200, fx("robots_star_block.txt"))})
        r = a.run(BASE + "/", fetch=make_fetch(files))
        self.assertEqual(by_id(r)["crawlers-answer"]["status"], "fail")
        self.assertTrue(all(not row["allowed"] for row in r["crawlers"]))

    def test_missing_robots_means_nothing_blocked(self):
        files = {k: v for k, v in GOOD.items() if not k.endswith("robots.txt")}
        c = by_id(a.run(BASE + "/", fetch=make_fetch(files)))
        self.assertEqual(c["crawlers-answer"]["status"], "pass")

    def test_js_shell_page(self):
        files = dict(GOOD, **{BASE + "/": (200, fx("js_shell.html"))})
        c = by_id(a.run(BASE + "/", fetch=make_fetch(files)))
        self.assertEqual(c["canonical"]["status"], "fail")
        self.assertEqual(c["meta-robots"]["status"], "fail")
        self.assertEqual(c["h1"]["status"], "warn")
        self.assertEqual(c["json-ld"]["status"], "fail")
        self.assertEqual(c["server-text"]["status"], "fail")
        self.assertEqual(c["description"]["status"], "warn")
        self.assertEqual(c["title"]["status"], "warn")

    def test_x_robots_tag_header_noindex(self):
        def fetch(url):
            r = make_fetch(GOOD)(url)
            if url == BASE + "/":
                r.headers = {"x-robots-tag": "noindex"}
            return r
        c = by_id(a.run(BASE + "/", fetch=fetch))
        self.assertEqual(c["meta-robots"]["status"], "fail")

    def test_page_404_stops_early(self):
        calls = []
        r = a.run(BASE + "/missing", fetch=make_fetch({}, calls))
        self.assertEqual(r["checks"][0]["status"], "fail")
        self.assertEqual(calls, [BASE + "/missing"])

    def test_one_request_per_url(self):
        calls = []
        a.run(BASE + "/", fetch=make_fetch(GOOD, calls))
        self.assertEqual(len(calls), len(set(calls)))
        self.assertEqual(len(calls), 4)

    def test_adds_scheme(self):
        calls = []
        a.run("bakery.example/", fetch=make_fetch(GOOD, calls))
        self.assertEqual(calls[0], "https://bakery.example/")

    def test_json_output_shape(self):
        r = a.run(BASE + "/", fetch=make_fetch(GOOD))
        again = json.loads(json.dumps(r))
        self.assertEqual(set(again), {"url", "final_url", "checks", "crawlers", "counts"})


class LlmsTests(unittest.TestCase):
    def _llms(self, status, body):
        return a.check_llms(a.Response(BASE + "/llms.txt", status, {}, body))

    def test_good(self):
        self.assertEqual(self._llms(200, fx("llms_good.txt")).status, "pass")

    def test_malformed(self):
        c = self._llms(200, fx("llms_bad.txt"))
        self.assertEqual(c.status, "warn")
        self.assertIn("heading", c.detail)

    def test_missing(self):
        self.assertEqual(self._llms(404, "").status, "warn")

    def test_html_soft_404(self):
        self.assertEqual(self._llms(200, "<!doctype html><html></html>").status, "warn")

    def test_empty(self):
        self.assertEqual(self._llms(200, "  \n").status, "fail")


class SitemapTests(unittest.TestCase):
    def test_page_listed_with_trailing_slash_difference(self):
        c = a.check_sitemap(a.Response("u", 200, {}, fx("sitemap.xml")), "u", BASE + "/menu/")
        self.assertEqual(c.status, "pass")

    def test_page_not_listed(self):
        c = a.check_sitemap(a.Response("u", 200, {}, fx("sitemap_other.xml")), "u", BASE + "/")
        self.assertEqual(c.status, "warn")

    def test_missing(self):
        self.assertEqual(a.check_sitemap(a.Response("u", 404), "u", BASE + "/").status, "fail")

    def test_index_follows_child(self):
        files = {BASE + "/sitemap-0.xml": (200, fx("sitemap.xml"))}
        c = a.check_sitemap(a.Response("u", 200, {}, fx("sitemap_index.xml")), "u", BASE + "/", make_fetch(files))
        self.assertEqual(c.status, "pass")

    def test_sitemap_from_robots_line_is_used(self):
        robots = "User-agent: *\nDisallow:\nSitemap: https://bakery.example/maps/all.xml\n"
        files = {k: v for k, v in GOOD.items() if not k.endswith("sitemap.xml")}
        files[BASE + "/robots.txt"] = (200, robots)
        files[BASE + "/maps/all.xml"] = (200, fx("sitemap.xml"))
        self.assertEqual(by_id(a.run(BASE + "/", fetch=make_fetch(files)))["sitemap"]["status"], "pass")


class OutputTests(unittest.TestCase):
    def test_text_report(self):
        text = a.render_text(a.run(BASE + "/", fetch=make_fetch(GOOD)))
        self.assertIn("[PASS] Page returns 200", text)
        self.assertIn("OAI-SearchBot", text)
        self.assertTrue(text.rstrip().endswith("12 pass, 0 warn, 0 fail"))

    def test_user_agent_names_the_skill(self):
        self.assertIn("aeo-check", a.USER_AGENT)
        self.assertEqual(a.TIMEOUT, 10)


if __name__ == "__main__":
    unittest.main()
