#!/usr/bin/env python3
"""aeo_check: can AI answer engines read and cite this page?

Fetches one page plus /robots.txt, /llms.txt and one sitemap, and reports a
pass, warn or fail per check. Standard library only. One request per URL.

    python3 aeo_check.py https://example.com/
    python3 aeo_check.py https://example.com/ --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

VERSION = "1.0"
USER_AGENT = f"rogue-aeo-check/{VERSION} (+https://roguedigital.ai)"
TIMEOUT = 10
MAX_BYTES = 2_000_000

PASS, WARN, FAIL = "pass", "warn", "fail"

# (robots.txt token, role). Roles: search = decides if you appear in answers,
# user = fetches a page when a person asks, training = model training only.
# Vendor sources are listed in references/crawlers.md.
CRAWLERS = [
    ("GPTBot", "training"),
    ("OAI-SearchBot", "search"),
    ("ChatGPT-User", "user"),
    ("ClaudeBot", "training"),
    ("Claude-SearchBot", "search"),
    ("Claude-User", "user"),
    ("PerplexityBot", "search"),
    ("Google-Extended", "training"),
    ("Applebot-Extended", "training"),
    ("CCBot", "training"),
]


@dataclass
class Response:
    url: str
    status: int = 0
    headers: dict = field(default_factory=dict)
    body: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


@dataclass
class Check:
    id: str
    status: str
    summary: str
    detail: str = ""


def http_fetch(url: str) -> Response:
    """The default fetch layer: one GET, 10 second timeout, body capped."""
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain,application/xml,*/*"}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read(MAX_BYTES)
            charset = r.headers.get_content_charset() or "utf-8"
            return Response(r.geturl(), r.status, {k.lower(): v for k, v in r.headers.items()},
                            raw.decode(charset, errors="replace"))
    except urllib.error.HTTPError as e:
        return Response(url, e.code, {k.lower(): v for k, v in e.headers.items()}, "", f"HTTP {e.code}")
    except Exception as e:  # network, DNS, TLS, timeout
        return Response(url, 0, {}, "", f"{type(e).__name__}: {e}")


# ---------- robots.txt ----------

def parse_robots(text: str):
    """Return (groups, sitemaps). Each group is {'agents': [...], 'rules': [(allow, path)]}."""
    groups, sitemaps, cur, last_was_agent = [], [], None, False
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            if cur is None or not last_was_agent:
                cur = {"agents": [], "rules": []}
                groups.append(cur)
            cur["agents"].append(value.lower())
            last_was_agent = True
            continue
        last_was_agent = False
        if key == "sitemap":
            sitemaps.append(value)
        elif key in ("allow", "disallow") and cur is not None:
            if value or key == "allow":
                cur["rules"].append((key == "allow", value))
    return groups, sitemaps


def _rule_matches(pattern: str, path: str) -> bool:
    if pattern == "":
        return False
    anchored = pattern.endswith("$")
    if anchored:
        pattern = pattern[:-1]
    regex = ".*".join(re.escape(p) for p in pattern.split("*"))
    return re.match(regex + ("$" if anchored else ""), path) is not None


def robots_verdict(groups, token: str, path: str = "/"):
    """Is `token` allowed to fetch `path`? Returns (allowed, matched_group_name)."""
    token = token.lower()
    group, via = None, ""
    for g in groups:
        if token in g["agents"]:
            group, via = g, token
            break
    if group is None:
        for g in groups:
            if "*" in g["agents"]:
                group, via = g, "*"
                break
    if group is None:
        return True, "no rule"
    best_len, allowed = -1, True
    for allow, pattern in group["rules"]:
        if _rule_matches(pattern, path):
            n = len(pattern)
            if n > best_len or (n == best_len and allow):
                best_len, allowed = n, allow
    return allowed, via


def check_crawlers(robots: Response, path: str):
    """Return (checks, per-crawler rows)."""
    rows = []
    if robots.status == 404 or robots.status == 410:
        groups = []
        note = "no robots.txt, so nothing is blocked"
    elif not robots.ok:
        return [Check("robots", WARN, f"robots.txt could not be read ({robots.error or robots.status})")], []
    else:
        groups, _ = parse_robots(robots.body)
        note = ""
    for token, role in CRAWLERS:
        allowed, via = robots_verdict(groups, token, path)
        rows.append({"crawler": token, "role": role, "allowed": allowed, "via": via})
    checks = []
    blocked_search = [r["crawler"] for r in rows if not r["allowed"] and r["role"] in ("search", "user")]
    blocked_train = [r["crawler"] for r in rows if not r["allowed"] and r["role"] == "training"]
    if blocked_search:
        checks.append(Check("crawlers-answer", FAIL,
                            "Blocks crawlers that decide whether you appear in AI answers: " + ", ".join(blocked_search),
                            "Search and user-request crawlers fetch pages so engines can cite them. Blocking them removes you from those answers."))
    else:
        checks.append(Check("crawlers-answer", PASS, "Search and user-request AI crawlers are allowed", note))
    if blocked_train:
        checks.append(Check("crawlers-training", WARN,
                            "Blocks training-only crawlers: " + ", ".join(blocked_train),
                            "This is a legitimate choice. Make sure it is a choice and not a leftover rule."))
    else:
        checks.append(Check("crawlers-training", PASS, "Training crawlers are allowed", note))
    return checks, rows


# ---------- llms.txt ----------

def check_llms(llms: Response) -> Check:
    if llms.status in (404, 410) or (not llms.ok and not llms.status):
        return Check("llms-txt", WARN, "No llms.txt",
                     "Optional and cheap. A short Markdown map of your best pages for AI tools.")
    if not llms.ok:
        return Check("llms-txt", WARN, f"llms.txt returned {llms.status}")
    body = llms.body.strip()
    if re.match(r"(?i)<!doctype html|<html", body):
        return Check("llms-txt", WARN, "No llms.txt (the URL returns a web page, not a text file)")
    lines = [l for l in body.splitlines() if l.strip()]
    if not lines:
        return Check("llms-txt", FAIL, "llms.txt is empty")
    problems = []
    if not lines[0].startswith("# "):
        problems.append("first line should be a '# Name' heading")
    if not any(l.startswith(">") for l in lines):
        problems.append("no '> summary' line")
    links = re.findall(r"\]\([^)\s]+\)|https?://[^\s)>\]]+|(?<![\w/])/[A-Za-z0-9][\w./-]*", body)
    if not links:
        problems.append("no links or paths to your key pages")
    if problems:
        return Check("llms-txt", WARN, "llms.txt present but not well formed", "; ".join(problems))
    return Check("llms-txt", PASS, f"llms.txt present and well formed ({len(links)} links)")


# ---------- HTML ----------

class PageParser(HTMLParser):
    SKIP = {"script", "style", "noscript", "template", "svg", "head"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.in_title = False
        self.metas = []          # list of attr dicts
        self.canonicals = []
        self.h1 = 0
        self.jsonld = []
        self._ld = None
        self._skip = 0
        self.words = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            self.metas.append(a)
        elif tag == "link" and "canonical" in a.get("rel", "").lower().split():
            self.canonicals.append(a.get("href", "").strip())
        elif tag == "h1":
            self.h1 += 1
        elif tag == "script" and "ld+json" in a.get("type", "").lower():
            self._ld = []
        if tag in self.SKIP and tag != "head":
            self._skip += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "script" and self._ld is not None:
            self.jsonld.append("".join(self._ld))
            self._ld = None
        if tag in self.SKIP and tag != "head" and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self._ld is not None:
            self._ld.append(data)
        elif not self._skip and not self.in_title:
            self.words += len(data.split())

    def meta(self, name: str) -> str:
        for m in self.metas:
            if m.get("name", "").lower() == name:
                return m.get("content", "")
        return ""


def parse_html(html: str) -> PageParser:
    p = PageParser()
    p.feed(html)
    p.close()
    return p


def _types(node, out):
    if isinstance(node, list):
        for n in node:
            _types(n, out)
    elif isinstance(node, dict):
        t = node.get("@type")
        if isinstance(t, str):
            out.append(t)
        elif isinstance(t, list):
            out.extend(x for x in t if isinstance(x, str))
        for v in node.values():
            if isinstance(v, (list, dict)):
                _types(v, out)


ENTITY_TYPES = {"Organization", "LocalBusiness", "Person", "Corporation", "ProfessionalService",
                "Store", "OnlineStore", "WebSite"}


def check_page(page: Response, p: PageParser):
    checks = []
    final = urlsplit(page.url)

    if page.ok:
        detail = f"Final URL: {page.url}" if page.url else ""
        checks.append(Check("page-status", PASS, f"Page returns {page.status}", detail))
    else:
        checks.append(Check("page-status", FAIL, f"Page returned {page.status or 'no response'}", page.error))
        return checks

    # canonical
    n = len(p.canonicals)
    if n == 0:
        checks.append(Check("canonical", WARN, "No canonical link"))
    elif n > 1 and len(set(p.canonicals)) > 1:
        checks.append(Check("canonical", FAIL, f"{n} different canonical links, there should be exactly one"))
    elif n > 1:
        checks.append(Check("canonical", WARN, f"Canonical link repeated {n} times, there should be exactly one"))
    else:
        target = urljoin(page.url, p.canonicals[0])
        t = urlsplit(target)
        same = (t.netloc.lower(), t.path.rstrip("/")) == (final.netloc.lower(), final.path.rstrip("/"))
        if same:
            checks.append(Check("canonical", PASS, "One canonical link, pointing at this page"))
        else:
            checks.append(Check("canonical", WARN, "One canonical link, but it points at another URL", target))

    # robots directives
    directives = (p.meta("robots") + "," + p.meta("googlebot") + "," + page.headers.get("x-robots-tag", "")).lower()
    if "noindex" in directives or "none" in re.split(r"[,\s]+", directives):
        checks.append(Check("meta-robots", FAIL, "Page is set to noindex", directives.strip(", ")))
    elif "nosnippet" in directives or re.search(r"max-snippet:\s*0", directives):
        checks.append(Check("meta-robots", WARN, "Snippets are switched off, engines may not quote this page", directives.strip(", ")))
    else:
        checks.append(Check("meta-robots", PASS, "No noindex or nosnippet directive"))

    # title
    title = " ".join(p.title.split())
    if not title:
        checks.append(Check("title", FAIL, "No title"))
    elif len(title) < 15 or len(title) > 70:
        checks.append(Check("title", WARN, f"Title is {len(title)} characters (aim for 15 to 70)", title))
    else:
        checks.append(Check("title", PASS, f"Title is {len(title)} characters", title))

    # description
    desc = " ".join(p.meta("description").split())
    if not desc:
        checks.append(Check("description", WARN, "No meta description"))
    elif len(desc) < 70 or len(desc) > 160:
        checks.append(Check("description", WARN, f"Description is {len(desc)} characters (aim for 70 to 160)", desc))
    else:
        checks.append(Check("description", PASS, f"Description is {len(desc)} characters", desc))

    # H1
    if p.h1 == 1:
        checks.append(Check("h1", PASS, "Exactly one H1"))
    elif p.h1 == 0:
        checks.append(Check("h1", FAIL, "No H1 in the server HTML"))
    else:
        checks.append(Check("h1", WARN, f"{p.h1} H1 headings, use one"))

    # JSON-LD
    good, bad, types = 0, 0, []
    for block in p.jsonld:
        try:
            _types(json.loads(block), types)
            good += 1
        except (ValueError, RecursionError):
            bad += 1
    uniq = sorted(set(types))
    if not p.jsonld:
        checks.append(Check("json-ld", FAIL, "No JSON-LD structured data"))
    elif bad and not good:
        checks.append(Check("json-ld", FAIL, f"{bad} JSON-LD block(s), none parse"))
    elif bad:
        checks.append(Check("json-ld", WARN, f"{good} JSON-LD block(s) parse, {bad} do not", ", ".join(uniq)))
    elif not ENTITY_TYPES & set(uniq):
        checks.append(Check("json-ld", WARN, f"{good} JSON-LD block(s) parse, but none names the business or site",
                            "Types: " + (", ".join(uniq) or "none")))
    else:
        checks.append(Check("json-ld", PASS, f"{good} JSON-LD block(s) parse", "Types: " + ", ".join(uniq)))

    # words in server HTML
    w = p.words
    if w >= 300:
        checks.append(Check("server-text", PASS, f"{w} words of text in the server HTML"))
    elif w >= 100:
        checks.append(Check("server-text", WARN, f"Only {w} words in the server HTML (aim for 300 or more)"))
    else:
        checks.append(Check("server-text", FAIL, f"Only {w} words in the server HTML",
                            "Most AI crawlers do not run JavaScript. If the text appears only in the browser, they see an empty page."))
    return checks


# ---------- sitemap ----------

def _norm(u: str) -> tuple:
    s = urlsplit(u.strip())
    return (s.netloc.lower().removeprefix("www."), s.path.rstrip("/") or "/", s.query)


MAX_CHILD_SITEMAPS = 3


def check_sitemap(sm: Response, sm_url: str, page_url: str, fetch=None) -> Check:
    if not sm.ok:
        return Check("sitemap", FAIL if sm.status in (0, 404, 410) else WARN,
                     f"No sitemap at {sm_url}" if sm.status in (0, 404, 410) else f"Sitemap returned {sm.status}")
    body = sm.body
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", body)
    if not locs:
        return Check("sitemap", WARN, "Sitemap found but no <loc> entries could be read", sm_url)
    if "<sitemapindex" in body:
        if fetch is None:
            return Check("sitemap", WARN, f"Sitemap index with {len(locs)} child sitemaps")
        wanted, seen = _norm(page_url), 0
        for child in locs[:MAX_CHILD_SITEMAPS]:
            r = fetch(child)
            kids = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", r.body) if r.ok else []
            seen += len(kids)
            if wanted in {_norm(x) for x in kids}:
                return Check("sitemap", PASS, f"Sitemap index lists this page ({seen} URLs read)", sm_url)
        more = len(locs) - MAX_CHILD_SITEMAPS
        note = f"Read the first {MAX_CHILD_SITEMAPS} of {len(locs)} child sitemaps." if more > 0 else ""
        return Check("sitemap", WARN, f"Sitemap index found but this page is not in the {seen} URLs read", note)
    if _norm(page_url) in {_norm(x) for x in locs}:
        return Check("sitemap", PASS, f"Sitemap lists this page ({len(locs)} URLs)", sm_url)
    return Check("sitemap", WARN, f"Sitemap found ({len(locs)} URLs) but this page is not in it", sm_url)


# ---------- run ----------

def run(url: str, fetch=http_fetch) -> dict:
    if not re.match(r"^https?://", url):
        url = "https://" + url
    page = fetch(url)
    origin = "{0.scheme}://{0.netloc}".format(urlsplit(page.url or url))
    result = {"url": url, "final_url": page.url, "checks": [], "crawlers": []}
    if not page.ok:
        result["checks"] = [asdict(c) for c in check_page(page, PageParser())]
        return finish(result)

    parser = parse_html(page.body)
    robots = fetch(origin + "/robots.txt")
    llms = fetch(origin + "/llms.txt")
    path = urlsplit(page.url).path or "/"
    if urlsplit(page.url).query:
        path += "?" + urlsplit(page.url).query

    checks = check_page(page, parser)
    crawler_checks, rows = check_crawlers(robots, path)
    checks = checks[:1] + crawler_checks + [check_llms(llms)] + checks[1:]

    sm_url = origin + "/sitemap.xml"
    if robots.ok:
        _, listed = parse_robots(robots.body)
        if listed:
            sm_url = urljoin(origin + "/", listed[0])
    checks.append(check_sitemap(fetch(sm_url), sm_url, page.url, fetch))

    result["checks"] = [asdict(c) for c in checks]
    result["crawlers"] = rows
    return finish(result)


def asdict(c: Check) -> dict:
    return {"id": c.id, "status": c.status, "summary": c.summary, "detail": c.detail}


def finish(result: dict) -> dict:
    counts = {PASS: 0, WARN: 0, FAIL: 0}
    for c in result["checks"]:
        counts[c["status"]] += 1
    result["counts"] = counts
    return result


def render_text(result: dict) -> str:
    out = [f"AEO check: {result['url']}"]
    if result["final_url"] and result["final_url"] != result["url"]:
        out.append(f"Final URL: {result['final_url']}")
    out.append("")
    tag = {PASS: "PASS", WARN: "WARN", FAIL: "FAIL"}
    for c in result["checks"]:
        out.append(f"[{tag[c['status']]}] {c['summary']}")
        if c["detail"]:
            out.append(f"       {c['detail']}")
    if result["crawlers"]:
        out += ["", "AI crawlers in robots.txt:"]
        for r in result["crawlers"]:
            verdict = "allowed" if r["allowed"] else "BLOCKED"
            out.append(f"  {r['crawler']:<19} {r['role']:<9} {verdict} ({r['via']})")
    n = result["counts"]
    out += ["", f"{n[PASS]} pass, {n[WARN]} warn, {n[FAIL]} fail"]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check if a page is easy for AI answer engines to read and cite.")
    ap.add_argument("url")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = ap.parse_args(argv)
    result = run(args.url)
    print(json.dumps(result, indent=2) if args.json else render_text(result))
    return 2 if result["checks"] and result["checks"][0]["id"] == "page-status" and result["checks"][0]["status"] == FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
