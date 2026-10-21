# AI crawlers the script checks

Each name below is the token you put after `User-agent:` in robots.txt. Each description comes from the vendor's own page, read on 21 October 2026. Vendors change these pages, so check the source before you act on a rule.

The script groups the crawlers by what blocking them costs you.

- **Search**: finds pages so the engine can show and cite them. Block these and you drop out of that engine's answers.
- **User**: fetches a page when a person asks a question about it. Block these and the assistant cannot read your page for that person.
- **Training**: collects content to train models. Blocking is a business choice and does not remove you from answers.

| Token | Role | What the vendor says | Source |
| --- | --- | --- | --- |
| `OAI-SearchBot` | search | Used so sites appear in ChatGPT search features. | https://developers.openai.com/api/docs/bots |
| `ChatGPT-User` | user | Used for some user-initiated actions in ChatGPT. The page says robots.txt rules may not apply to it. | https://developers.openai.com/api/docs/bots |
| `GPTBot` | training | Collects content that may be used to train OpenAI's models. | https://developers.openai.com/api/docs/bots |
| `Claude-SearchBot` | search | Crawls content to improve the quality of search results shown to users. | https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler |
| `Claude-User` | user | Visits a site when a person asks Claude a question. | https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler |
| `ClaudeBot` | training | Collects web content that may be used to train Anthropic's models. | https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler |
| `PerplexityBot` | search | Surfaces and links websites in Perplexity search results. The page says it is not used to crawl for model training. | https://docs.perplexity.ai/docs/resources/perplexity-crawlers |
| `Google-Extended` | training | A robots.txt token only, with no user agent string of its own. Controls whether Google may use crawled content for Gemini. The page says it does not affect inclusion in Google Search. | https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers |
| `Applebot-Extended` | training | A secondary token that controls whether Apple may use crawled content to train its foundation models. It does not crawl, and does not change search inclusion. | https://support.apple.com/en-us/119829 |
| `CCBot` | training | The Common Crawl crawler. Block it with `User-agent: CCBot` and `Disallow: /`. | https://commoncrawl.org/ccbot |

## Notes

- Perplexity also lists `Perplexity-User` for user-initiated fetches. The page says it generally ignores robots.txt, so the script does not test it.
- Applebot (the plain crawler) feeds Apple search features and follows its own rules. The script tests only the `-Extended` token, which is the AI training control.
- Google says blocking `Google-Extended` does not affect inclusion in Google Search. Google's Search crawler is a separate thing.
- Not on the list, not tested: other crawlers appear all the time. Add a row to `CRAWLERS` in `scripts/aeo_check.py` and a row here, with its source.

## Check the sources still answer

```bash
for u in \
  https://developers.openai.com/api/docs/bots \
  https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler \
  https://docs.perplexity.ai/docs/resources/perplexity-crawlers \
  https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers \
  https://support.apple.com/en-us/119829 \
  https://commoncrawl.org/ccbot; do
  curl -s -o /dev/null -L -w "%{http_code} $u\n" "$u"
done
```
