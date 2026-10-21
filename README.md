# claude-skills

Free Claude skills from Rogue Digital, a UK AI and engineering consultancy.

## Skills

| Skill | What it does |
| --- | --- |
| [ai-policy-builder](skills/ai-policy-builder/) | Drafts a plain-English AI use policy for a small UK business. |
| [speed-to-lead-audit](skills/speed-to-lead-audit/) | Checks how fast and how well a business answers new enquiries. |
| [aeo-check](skills/aeo-check/) | Checks whether a site is easy for AI answer engines to read and cite. |

## Install

**Copy a folder.** Copy any folder from `skills/` into `~/.claude/skills/`. Claude Code picks it up in the next session.

**Use the repo as a plugin marketplace.** In your shell:

```bash
claude plugin marketplace add RogueDigital/claude-skills
claude plugin install rogue-skills@rogue-digital
```

Or inside a session: `/plugin marketplace add RogueDigital/claude-skills`, then `/plugin install rogue-skills@rogue-digital`.

The scripts use the Python standard library only (Python 3.11 or later). Nothing else to install.

## Checks

`bash scripts/check.sh` checks the skill frontmatter, scans for secrets and runs each skill's tests.

## About Rogue Digital

Rogue Digital Ltd is a UK AI and engineering consultancy. We build AI agents and automation, web and e-commerce sites, and help businesses get found in AI search. These skills are small tools we think are useful on their own. Written by Jamie Buchanan. More at [roguedigital.ai](https://roguedigital.ai/?utm_source=github&utm_medium=referral&utm_campaign=rogue-growth-2026q4&utm_content=claude-skills).

## Licence

MIT. See [LICENSE](LICENSE).
