---
name: aeo-check
description: Checks whether a website is easy for AI answer engines (ChatGPT, Claude, Perplexity, Google AI) to read and cite, then lists the five fixes that matter most. Runs a standard-library Python script that tests robots.txt for AI crawlers, llms.txt, canonical, meta robots, title, description, H1, JSON-LD and server-rendered text, and the sitemap. Then reviews what a script cannot judge. Use when someone asks "can AI find my site", "why is my business not cited by ChatGPT", or for an AEO, GEO or AI search audit of one page.
---

# AEO check

Answer engine optimisation (AEO) means making a page easy for AI tools to read, trust and quote. This skill checks one page and its site-level files, then gives a short list of fixes.

The script covers what a machine can test. You cover what needs judgement. Do both.

## When to use it

- "Can ChatGPT or Perplexity read my site?"
- "Why does AI never mention my business?"
- "Audit this page for AI search."

Do not use it to promise rankings or citations. Nobody can. It removes common reasons a page gets skipped.

## Step 1: run the script

```bash
python3 scripts/aeo_check.py https://example.com/
```

Add `--json` for machine-readable output. Python 3.11 or later, nothing to install.

It makes one request each to the page, `/robots.txt`, `/llms.txt` and the sitemap (the one named in robots.txt, else `/sitemap.xml`; for a sitemap index it reads up to three child sitemaps). It identifies itself as `rogue-aeo-check`, times out at 10 seconds and crawls nothing else. Only run it on a site you own, or one you have permission to check.

Pass the page you care about, not only the homepage. A product or service page tells you more.

Each check comes back pass, warn or fail. `references/checks.md` says what each one means. `references/crawlers.md` lists the AI crawlers and where each name comes from.

If the page does not load, stop and report that. Nothing else can be judged.

## Step 2: the judgement part

Read the page text yourself, or ask for it if you cannot reach it. Answer each question with evidence from the page, not a guess.

1. **Does it answer the question straight away?** Look at the first two or three lines under the H1. A visitor, or an engine, should get the answer there. Scene-setting first is a fail.
2. **Is there an author and a date?** A named person, a role, and a published or updated date. For advice on money, health or law, this matters more.
3. **Are the claims sourced?** Numbers, rankings and "studies show" need a source or an honest "in our experience". Flag any figure that looks invented. Do not invent replacements.
4. **Is the business clear?** Name, place, what it does and who for, on the page or one click away, and the same wherever it appears. An engine cannot cite a business it cannot name.
5. **Can a passage be lifted?** Pick a paragraph. If it still makes sense quoted alone, good. If it says "as above" or "this", it does not.

If the script was blocked from the site, or the text only appears with JavaScript, say what you could not check.

## Step 3: report

Write the report in this order, in plain English:

1. One line: how ready the page is, in words ("easy to read, but blocks one answer crawler"). No made-up score.
2. The script results that failed or warned, one line each.
3. The judgement findings, one line each, with a quote or a pointer to where on the page.
4. **The five fixes that matter most for this site.** Number them. Order by effect:
   - Anything that blocks access comes first: a blocked search or user crawler, noindex, a page that is empty without JavaScript.
   - Then the entity and answer fixes: a clear business description, a direct answer at the top, an author and date.
   - Then the tidy-ups: canonical, JSON-LD, title and description, sitemap, llms.txt.

   Each fix says what to change, where, and how you will know it worked. Fewer than five is fine if that is all there is. Never pad.

Keep the whole report under one page. Do not suggest FAQPage markup or fake statistics.

Made by Rogue Digital, https://roguedigital.ai
