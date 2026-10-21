---
name: speed-to-lead-audit
description: Measures how fast a business answers its own enquiries and says what to fix first. Use when an owner or ops lead says enquiries go cold, replies are slow, leads get forgotten, or asks "how quickly do we reply?". Runs a small offline script on a CSV export of enquiries (arrival time and first reply time) to give the median, 90th percentile, share answered within 5 minutes, 1 hour and the same working day, the share never answered, and in hours versus out of hours. Then walks a manual checklist for what the data cannot show and ranks the top three fixes. Does not contact anyone.
---

# Speed to lead audit

Finds out how long your own enquiries wait for a first reply, then tells you what to fix first. It uses your own numbers, from your own export. It does not send anything to anyone.

## When to use it

Use it when someone says things like:

- "Enquiries go cold before we get back to them."
- "I think we are slow to reply, but I do not know how slow."
- "Some enquiries never get an answer."
- "We get enquiries in the evening and at weekends and I do not know what happens to them."

Do not use it to test another business. It audits the enquiries the user's own business has already received.

## Why the numbers matter

Harvard Business Review's research on online sales leads concluded that most companies are not responding nearly fast enough: https://hbr.org/2011/03/the-short-life-of-online-sales-leads

This skill does not rely on any published average. Your own times, over your own enquiries, are the useful figure. If you want to know whether speed affects how many enquiries you win, add an outcome column to the export and compare your own results after a few months.

## Step 1: get the data

You need one row per enquiry, with two times:

- **Created:** when the enquiry arrived.
- **First response:** when a person first replied. Leave it blank if nobody has.

Where to find them, in general terms:

- **A CRM or helpdesk:** export the contacts or tickets list as CSV. Look for a created date and a first reply, first contact or first activity date. If there is no first reply field, export the activity log and take the earliest outgoing message per enquiry.
- **A shared inbox:** there is rarely a built-in export. Copy the last 20 to 40 enquiries into a sheet by hand: the time each arrived, and the time of the first human reply in the thread.
- **A form tool or a website form:** export the submissions with their timestamps. Add a column for the time of the first reply and fill it in from the inbox.
- **A shared tracker or spreadsheet:** it probably has both columns already. Save it as CSV.

Rules for the file:

- The first row is a header with column names.
- Times look like `2026-03-10 14:05` or `10/03/2026 14:05`. Day first, not month first.
- A time with no timezone is read as UK local time. Clock changes are handled.
- Use at least 20 enquiries. Use the last 90 days if you have the volume, so the answer reflects how the business works now.
- Strip out spam and test submissions first.
- Remove any personal details the audit does not need. The script only needs the two time columns, so delete the name, email and phone columns before sharing the file with anyone.

Ask the user for the file path, and for the names of the two time columns.

## Step 2: run the script

```bash
python3 scripts/lead_timing.py enquiries.csv --created "Created" --responded "First reply"
```

Options:

- `--hours "Mon-Fri 09:00-17:30"` sets working hours. This is the default. Change it to match the business, for example `"Mon-Sat 08:00-18:00"`.
- `--timezone Europe/London` is the default. It applies to times with no offset.
- `--json` prints machine-readable output instead of text.

It reads only the file you give it, needs no install beyond Python 3.11 or later, and makes no network calls. On Windows you may need `pip install tzdata` for timezone data.

What the output means:

- **Median and 90th percentile** are measured in real elapsed time, from arrival to first reply, over answered enquiries only. The 90th percentile is the wait that nine in ten enquiries beat. It shows the slow tail that the median hides.
- **Within 5 minutes, within 1 hour, same working day** are shares of all enquiries, so an enquiry nobody answered counts against all three.
- **Same working day** means answered by closing time on the working day the enquiry belongs to. An enquiry that arrives out of hours belongs to the next working day.
- **Never answered** is the share with a blank first response.
- **In hours versus out of hours** splits by when the enquiry arrived. Read the two blocks separately. A good in-hours result can hide a poor out-of-hours one.
- **Skipped rows** could not be timed (a missing date, a reply earlier than the enquiry). Fix those in the file and run it again.

Report the result back in plain words first, then the figures. For example: "Half your evening enquiries wait until the next afternoon, and one in ten is never answered."

A sample file is in `references/sample-enquiries.csv`. All of its data is made up.

## Step 3: check what the data cannot show

The numbers show how long people waited. They do not show why. Ask the user about each of these, and note the answers:

1. **Instant acknowledgement.** When an enquiry arrives, does the sender get an automatic message within a minute, saying it arrived, who will reply and by when? Is it purely administrative, with no selling in it?
2. **One named owner.** Does every enquiry have one named person responsible for the first reply, or does it go to "the team" or a shared mailbox?
3. **Out-of-hours handling.** What does someone who writes at 19:00 on a Friday see? Do they know when a person will reply? On Monday morning, does the owner start with a list ordered by arrival time, oldest first?
4. **Reminders.** If nobody has replied after a set time, does anything nudge the owner, and then someone senior? Or does it rely on memory?
5. **Where the owner hears about it.** Does the owner get a message on their phone, or only a line in an inbox they may not be looking at?
6. **A record.** Is there one row per enquiry somewhere with arrived, owner, replied and outcome, so this audit can be repeated in a month?
7. **Emergencies.** If some enquiries cannot wait, is a phone number shown next to the form, with a plain note that it is for emergencies?

## Step 4: the top three fixes

Pick at most three from `references/fixes.md`, ranked by the numbers. Use these rules in order, and stop at three:

1. **Anything never answered (more than 0%).** Fix: the reminder, then one named owner. A timer is what catches an enquiry that was opened and forgotten. If you can only do one thing, do this.
2. **A slow tail.** If the 90th percentile is more than about ten times the median, or the same working day share is below 90%, fix: the reminder, with a second nudge to someone senior.
3. **In-hours median over an hour, or under half answered within an hour.** Fix: one named owner, with a message to their phone, and an instant acknowledgement to buy time.
4. **Out of hours.** If more than a quarter of enquiries arrive out of hours and their same working day share is below the in-hours one, fix: the out-of-hours reply and the Monday morning list.
5. **Slow first drafts.** If replies are slow even with an owner and reminders in place, fix: an AI-drafted first reply that a person checks and sends.
6. **No record.** If the checklist shows no tracker, fix: the weekly measure, so the next audit is easy.

Write the three fixes in plain English. For each: the number that triggered it, the fix in one sentence, the effort, and how to check it worked. Then give a target in plain words, such as "every enquiry has a reply from a person by the end of the next working day", and suggest running this audit again in four weeks.

Do not promise a result. Say what the data shows and what is likely to help, and label anything you are inferring as an inference.

## What not to do

- Do not tell the user to submit test enquiries to other businesses.
- Do not let an AI tool send replies by itself. A person reads and sends them. Never send prices or quotes unchecked.
- Do not quote a published statistic unless you have opened the source and can link to it.

Made by Rogue Digital, https://roguedigital.ai
