# What each check means

Each check reports pass, warn or fail. Fail means an engine is likely to miss or skip the page. Warn means a weakness worth fixing. None of these guarantees a citation: they remove reasons not to be cited.

## Access

**Page status.** The page must answer 200. Redirects are followed and the final URL is shown. If the page does not load, nothing else matters and the script stops.

**Search and user crawlers (robots.txt).** Fail if any of OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User or PerplexityBot is blocked from this page. These are the crawlers that fetch pages so assistants can show and cite them. A blanket `Disallow: /` under `User-agent: *` blocks them all. No robots.txt at all means nothing is blocked.

**Training crawlers (robots.txt).** Warn if GPTBot, ClaudeBot, Google-Extended, Applebot-Extended or CCBot is blocked. Many owners block these on purpose. The warning is there so it is a choice and not a leftover. See `crawlers.md`.

**Meta robots.** Fail on `noindex` in a meta tag or an `X-Robots-Tag` header. Warn on `nosnippet` or `max-snippet:0`, which tell engines not to quote the page.

**Sitemap.** Found through the `Sitemap:` line in robots.txt, else `/sitemap.xml`. Warn if the page is not listed. A sitemap helps crawlers find new and updated pages. If the sitemap is an index, the script reads up to three child sitemaps and no more.

**llms.txt.** A Markdown file at `/llms.txt`: a `# Name` heading, a `> summary` line, then links to your best pages. It is a proposal, not a standard every engine reads, so a missing file is only a warn. Cheap to add, and it makes you describe yourself in a few lines.

## Page content

**Server HTML text.** Counts the words in the HTML as served, before any JavaScript runs. Most AI crawlers do not run JavaScript. A page that fills in after load can look empty to them. Fail under 100 words, warn under 300.

**H1.** Exactly one, in the server HTML. It tells an engine what the page is about.

**Title and description.** Title 15 to 70 characters, description 70 to 160. Engines often use them to decide what a page is and how to summarise it. Treat the ranges as guides.

**Canonical.** Exactly one `rel="canonical"` link, pointing at this page. Several different canonicals leave engines guessing which URL to credit.

**JSON-LD.** Structured data in `<script type="application/ld+json">` blocks that parse. The script lists the `@type` values. It warns if no block names the business or site (Organization, LocalBusiness, Person, WebSite and similar), because that is how an engine ties the page to a real entity. FAQPage markup is not needed: it earns little for most sites, and a plain on-page question and answer works as well.

## What the script cannot judge

Whether the page answers the question quickly, who wrote it and when, whether the claims are sourced, and whether it is clear who the business is. `SKILL.md` covers these.
