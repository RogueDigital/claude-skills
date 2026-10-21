# Fixes

Each fix says what it costs in effort and how to check it worked. Effort is a rough guide for a small team using tools it already has. Check each fix by running the audit again after four weeks of enquiries.

## 1. Reminder when nobody has replied

**What it is.** A timer on every enquiry. If no reply is logged, the owner gets a nudge. Later, someone senior does too. At the end of the day, anything still waiting goes to the top of tomorrow's list, marked overdue.

A set of numbers you can keep:

- No reply after two working hours: the owner is nudged.
- No reply after four working hours: the owner and a director are both nudged.
- No reply by the end of the day: it tops tomorrow's list as overdue.

**Effort.** Low to medium. In a CRM it is a task with a due date. Without one, it is a scheduled check of a tracker that compares the arrived and replied columns. Half a day to a day to set up and test.

**How to check it worked.**
- The never answered share falls to 0%.
- The 90th percentile comes down towards the median.
- The same working day share rises above 90%.
- Deliberately leave one test enquiry from your own team unanswered and confirm the nudge arrives.

## 2. One named owner for every enquiry

**What it is.** An enquiry sent to "the team" belongs to nobody. Write down a rule that gives each one a single owner:

- By service or type of work.
- By area.
- By size, with big ones going straight to a director.
- A weekly rota for everything else.

Make the owner hear about it on their phone, not only in a shared inbox. The person on site mid-afternoon is not looking at the inbox.

**Effort.** Low. An hour to agree the rule and write it down. Another hour to set up the phone message, if the form tool or inbox supports it.

**How to check it worked.**
- Every row in the export has an owner.
- The in-hours median falls.
- Ask each owner whether they knew the enquiry was theirs. It should be yes every time.

## 3. Instant acknowledgement

**What it is.** An automatic message within a minute that confirms the enquiry arrived, says who will reply and by when, and asks nothing hard. It does not replace a real reply. It stops the sender wondering whether the form worked, and it sets the expectation for the real reply.

Keep it purely administrative. The ICO says messages sent for administrative or customer service purposes are not direct marketing, but a service message that includes direct marketing elements counts as direct marketing: https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/direct-marketing-guidance/identify-direct-marketing/ This is general information, not legal advice.

Treat the acknowledgement as a courtesy, not proof of delivery. Automatic emails can be caught by spam filters.

An example:

> Thanks, we have your enquiry about replacing the shop-front windows. A named person will reply today before 5pm. If it cannot wait, call us on [number].

**Effort.** Low. Many form tools and inboxes can send an automatic reply. Allow an hour to write the text and test it.

**How to check it worked.**
- Submit a test through your own form and confirm the message arrives, in the inbox and not in spam.
- Read the text and confirm it contains no selling.
- Over the next month, check that fewer people chase with "did you get my message?".

## 4. Out-of-hours reply and a Monday morning list

**What it is.** Enquiries do not arrive only between nine and five. The out-of-hours acknowledgement should say when a person will reply, and only promise what you can do:

> We are closed until 8am on Monday. A named person will reply by 10am.

Then make Monday morning work. The owner starts with a list ordered by arrival time, oldest first, not an inbox to sort. If you take emergency callouts, do not rely on a form for them. Put the phone number beside the form and say it is for emergencies.

You can add a booking link to the acknowledgement so the person can choose a call time. That turns waiting into something they control.

**Effort.** Low to medium. An hour for the text. Another hour or two for the ordered list, depending on the tool.

**How to check it worked.**
- Run the audit and look at the out-of-hours block. The same working day share should be close to the in-hours one.
- The out-of-hours 90th percentile should fall.
- Check the promise in the message: every out-of-hours enquiry is answered by the time it states.

## 5. AI-drafted first reply, sent by a person

**What it is.** A first reply is mostly assembly: answer the question that was asked, say what you need to know to price the job, and propose the next step. An AI model can read the enquiry alongside your own price list, service descriptions and a few past replies, and write a draft. A person reads, corrects and sends it.

Rules to keep it safe:

- **A person sends it.** A language model can state things that are not true. Anthropic's guidance on reducing hallucinations says its techniques "don't eliminate them entirely", and that critical information should always be validated: https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations
- **No unchecked prices or quotes.** The draft can say what a typical job involves. A figure goes out only when a person has put it there.
- **Show the source.** The draft should say which line of the price list or which past reply it drew on.
- **Mind the data.** Enquiries contain names, addresses and phone numbers. Use an AI service on business terms, not a personal account.

A good first reply has three parts: an answer, one question you need answered, and a next step.

**Effort.** Medium. A day to set up, collect the source material and test on past enquiries. Expect to tune the instructions over the first couple of weeks.

**How to check it worked.**
- Compare the time from arrival to first reply before and after, for the same owner.
- Read ten drafts and count how many needed a correction before sending. Track that number.
- Confirm no reply went out without a person's name against it.

## 6. A weekly measure

**What it is.** One row per enquiry in a shared tracker: arrived, owner, replied, outcome. Once a week, look at three numbers: the typical time to first reply, the slowest five, and how many enquiries had no reply after a full day. Put them on the agenda of your weekly meeting. Set the target in plain words, then tighten it once you are meeting it.

**Effort.** Low. An hour to set up the tracker, and ten minutes a week to read it. Re-running this audit on the export is the same measure, done monthly.

**How to check it worked.**
- The export for the next audit takes minutes, not an afternoon.
- The weekly meeting looks at the numbers every time.
- The outcome column fills in, so you can compare speed with wins using your own data.
