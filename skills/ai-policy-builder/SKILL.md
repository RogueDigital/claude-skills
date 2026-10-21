---
name: ai-policy-builder
description: Interviews a small UK business owner and writes a one-page AI use policy for their team, in plain English. Use when an owner or ops lead asks for an AI policy, AI acceptable use rules, or "what can my staff put into ChatGPT". Asks at most eight short questions in one go, fills a one-page template, then lists what to check with a solicitor or the ICO guidance. Not legal advice.
---

# AI policy builder

Writes a one-page AI use policy for a small UK team. One page is the point: people read it, remember it and can follow it without asking anyone.

## When to use it

Use it when someone says things like:

- "We need an AI policy."
- "Write acceptable use rules for AI."
- "What can my staff put into ChatGPT?"
- "Staff are using AI and I have nothing in writing."

Do not use it for a full governance framework, a data protection impact assessment, or a policy for a regulated firm that needs its regulator's wording. Say so and suggest a solicitor for those.

## Say this first

State plainly, in one sentence, before and after the policy: this is a starting point, not legal advice.

## Step 1: the interview

Ask all the questions in one message, numbered, and let the owner answer in one go. Keep each question short. Do not ask them one at a time.

1. How many people are on the team, and what does the business do (sector)?
2. Which AI tools do people use today, and which do you want to allow? (For example ChatGPT, Claude, Copilot, Gemini. Business or personal accounts?)
3. What data does the team handle? (Customer names and contact details, financial records, health or HR records, anything else sensitive.)
4. Do any client contracts have confidentiality terms or limits on using AI?
5. Who signs off a new tool, and how fast do they answer?
6. Is any of the work regulated? (For example financial services, legal, healthcare, or anything with its own regulator.)
7. Does any AI output go to customers, or does AI touch decisions about people (hiring, discipline, credit)?
8. When should the policy be reviewed? (Suggest six months from today if they have no view.)

If an answer is missing, make a sensible default, mark it in square brackets in the policy, and say which ones you guessed. Do not stall for more answers.

## Step 2: write the policy

1. Read `references/policy-template.md`.
2. Fill every placeholder from the answers. Keep the section order.
3. Tune the three parts that vary most:
   - **Tools:** name the tool and the account type. "ChatGPT Business, signed in with your company email" is a policy. "Use AI responsibly" is not.
   - **What goes in:** use the traffic light. Move items between amber and red to match their data and their client contracts. Anything under a confidentiality term is red unless the contract allows AI.
   - **Checking output:** name who reads quotes, contract wording, HR wording and advice before it goes out.
4. Cut anything that does not apply. If the sector is regulated, add one line saying the regulator's rules come first.
5. Keep it to one page: about 350 to 450 words. If it runs over, cut examples, not rules.
6. Write in plain UK English. Short sentences. No em or en dashes. No legal jargon the owner would not say out loud.

## Step 3: what to check

After the policy, add a short list headed "Before you roll this out". Include only what fits their answers:

- Have a solicitor read it, especially if the work is regulated or client contracts restrict AI.
- Check client contracts for confidentiality or AI clauses before staff use client material in any tool.
- If personal data goes into a tool, check the tool's data terms and whether you need a data processing agreement.
- If AI will be used at scale on customer records, or to make decisions about people, read the ICO guidance on when a data protection impact assessment is needed.
- Know the breach rule: a notifiable personal data breach goes to the ICO within 72 hours of becoming aware of it. The policy tells staff to report slips the same day.
- ICO guidance is under review after the Data (Use and Access) Act, so read the current version.

Use `references/uk-notes.md` for the points and links. Give the links, do not paraphrase them as legal fact.

## Step 4: hand over

Offer three habits that make it stick: read it with each new starter in ten minutes, pin it where the team already works, and put the review date in the diary now.

Close with the line: this is a starting point, not legal advice.

## Rules for the skill

- Never invent a law, a guidance page or a deadline. Use only what is in `references/uk-notes.md`.
- Never name a real client or person in the policy unless the owner gave the name for it.
- Do not claim a tool is safe or compliant. Say what its account type usually means and tell them to check its terms.
- If the owner says something that points to a serious problem (a past leak, a regulator contact), stop and tell them to speak to a solicitor.

Made by Rogue Digital, https://roguedigital.ai
