#!/usr/bin/env python3
"""Measure how fast a business answers its enquiries.

Reads a CSV export with one row per enquiry: a created time and a first
response time. Prints the count, the median and 90th percentile time to first
response, the share answered within 5 minutes, 1 hour and the same working
day, the share never answered, and a split for in hours versus out of hours.

It reads only the file it is given. It never contacts anyone.
Standard library only, Python 3.11 or later.
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
DEFAULT_HOURS = "Mon-Fri 09:00-17:30"
DEFAULT_TZ = "Europe/London"
UK_FORMATS = ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S")


class InputError(Exception):
    """A problem with the arguments or the file, reported without a traceback."""


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_hours(spec):
    """Parse 'Mon-Fri 09:00-17:30' into (set of weekday numbers, open, close)."""
    match = re.fullmatch(r"\s*([A-Za-z,\- ]+?)\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*", spec)
    if not match:
        raise InputError(f"cannot read working hours {spec!r}. Use a form like '{DEFAULT_HOURS}'.")
    days_part, open_text, close_text = match.groups()
    days = set()
    for chunk in days_part.replace(" ", "").split(","):
        bounds = [b[:3].lower() for b in chunk.split("-")]
        if not 1 <= len(bounds) <= 2 or any(b not in DAY_NAMES for b in bounds):
            raise InputError(f"cannot read the days in {spec!r}. Use names like Mon-Fri or Mon,Wed,Fri.")
        start = DAY_NAMES.index(bounds[0])
        end = DAY_NAMES.index(bounds[-1])
        span = range(start, end + 1) if start <= end else list(range(start, 7)) + list(range(0, end + 1))
        days.update(span)
    try:
        opens = time.fromisoformat(open_text.zfill(5))
        closes = time.fromisoformat(close_text.zfill(5))
    except ValueError as exc:
        raise InputError(f"cannot read the times in {spec!r}: {exc}") from exc
    if closes <= opens:
        raise InputError("closing time must be after opening time.")
    return days, opens, closes


def parse_time(text, tz):
    """Parse ISO 8601 or DD/MM/YYYY HH:MM into an aware datetime in tz.

    A time with no offset is taken as local time in tz. A time with an offset
    is converted to tz. Returns None when the text is not a date and time.
    """
    text = (text or "").strip()
    if not text:
        return None
    parsed = None
    for fmt in UK_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        if len(text) <= 10:  # a date with no time cannot be timed
            return None
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=tz)
    return parsed.astimezone(tz)


def read_rows(path, created_col, responded_col):
    """Return (list of (row number, created text, responded text), warnings)."""
    file = Path(path)
    if not file.is_file():
        raise InputError(f"file not found: {path}")
    raw = file.read_text(encoding="utf-8-sig", errors="replace")
    if not raw.strip():
        raise InputError(f"{path} is empty. Export the enquiries with a header row.")
    try:
        dialect = csv.Sniffer().sniff(raw[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(raw.splitlines(), dialect=dialect)
    headers = reader.fieldnames or []
    lookup = {h.strip().lower(): h for h in headers}
    keys = []
    for label, wanted in (("created", created_col), ("first response", responded_col)):
        key = lookup.get(wanted.strip().lower())
        if key is None:
            raise InputError(
                f"no column called {wanted!r} for the {label} time. "
                f"Columns found: {', '.join(headers) or 'none'}."
            )
        keys.append(key)
    rows = []
    for number, record in enumerate(reader, start=2):  # row 1 is the header
        if not any((v or "").strip() for v in record.values() if isinstance(v, str)):
            continue  # blank line
        rows.append((number, record.get(keys[0]), record.get(keys[1])))
    return rows


# ---------------------------------------------------------------------------
# Working time
# ---------------------------------------------------------------------------

def in_working_hours(moment, hours):
    days, opens, closes = hours
    return moment.weekday() in days and opens <= moment.timetz().replace(tzinfo=None) < closes


def same_working_day_deadline(created, hours, tz):
    """The close of the working day the enquiry belongs to.

    Inside hours or before opening on a working day: that day's close.
    After close, or on a non-working day: the close of the next working day.
    """
    days, _, closes = hours
    day = created.date()
    for _ in range(14):  # a fortnight is more than enough for any weekly pattern
        if day.weekday() in days:
            close = datetime.combine(day, closes, tzinfo=tz)
            if created < close:
                return close
        day += timedelta(days=1)
    raise InputError("no working day found in the working hours given.")


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def percentile(values, pct):
    """Linear interpolation between closest ranks. values must not be empty."""
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * pct / 100
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def pct_of(part, whole):
    return round(100 * part / whole, 1) if whole else None


def summarise(records):
    """records: list of dicts with minutes (None if never answered) and same_day (bool)."""
    total = len(records)
    answered = [r["minutes"] for r in records if r["minutes"] is not None]
    return {
        "count": total,
        "answered": len(answered),
        "never_answered": total - len(answered),
        "never_answered_pct": pct_of(total - len(answered), total),
        "median_minutes": round(median(answered), 1) if answered else None,
        "p90_minutes": round(percentile(answered, 90), 1) if answered else None,
        "within_5_min_pct": pct_of(sum(1 for m in answered if m <= 5), total),
        "within_1_hour_pct": pct_of(sum(1 for m in answered if m <= 60), total),
        "same_working_day_pct": pct_of(sum(1 for r in records if r["same_day"]), total),
    }


def analyse(rows, created_col, responded_col, hours_spec, tz_name):
    tz = ZoneInfo(tz_name)
    hours = parse_hours(hours_spec)
    records, skipped = [], []
    for number, created_text, responded_text in rows:
        created = parse_time(created_text, tz)
        if created is None:
            skipped.append({"row": number, "reason": "created time missing or not a date and time"})
            continue
        responded = None
        if (responded_text or "").strip():
            responded = parse_time(responded_text, tz)
            if responded is None:
                skipped.append({"row": number, "reason": "first response time is not a date and time"})
                continue
            if responded < created:
                skipped.append({"row": number, "reason": "first response is before the enquiry was created"})
                continue
        # Elapsed time is real time: compared in UTC, so clock changes count.
        minutes = None
        same_day = False
        if responded is not None:
            minutes = (responded.astimezone(timezone.utc) - created.astimezone(timezone.utc)).total_seconds() / 60
            same_day = responded <= same_working_day_deadline(created, hours, tz)
        records.append({
            "minutes": minutes,
            "same_day": same_day,
            "in_hours": in_working_hours(created, hours),
        })
    return {
        "timezone": tz_name,
        "working_hours": hours_spec,
        "columns": {"created": created_col, "first_response": responded_col},
        "skipped_rows": skipped,
        "overall": summarise(records),
        "in_hours": summarise([r for r in records if r["in_hours"]]),
        "out_of_hours": summarise([r for r in records if not r["in_hours"]]),
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def human(minutes):
    if minutes is None:
        return "n/a"
    if minutes < 60:
        return f"{minutes:.0f} min"
    if minutes < 48 * 60:
        return f"{minutes / 60:.1f} hours"
    return f"{minutes / 1440:.1f} days"


def show_pct(value):
    return "n/a" if value is None else f"{value:.1f}%"


def render_text(result):
    lines = [
        "Speed to lead",
        f"Working hours: {result['working_hours']} ({result['timezone']})",
        "Times are real elapsed time from the enquiry arriving to the first response.",
        "Median and 90th percentile cover answered enquiries only.",
        "Shares are of all enquiries, so an unanswered one counts against every share.",
        "",
    ]
    for key, title in (("overall", "All enquiries"), ("in_hours", "Arrived in hours"),
                       ("out_of_hours", "Arrived out of hours")):
        s = result[key]
        lines.append(f"{title}: {s['count']}")
        if s["count"] == 0:
            lines.append("  none")
            lines.append("")
            continue
        lines += [
            f"  Median time to first response:  {human(s['median_minutes'])}",
            f"  90th percentile:                {human(s['p90_minutes'])}",
            f"  Answered within 5 minutes:      {show_pct(s['within_5_min_pct'])}",
            f"  Answered within 1 hour:         {show_pct(s['within_1_hour_pct'])}",
            f"  Answered the same working day:  {show_pct(s['same_working_day_pct'])}",
            f"  Never answered:                 {show_pct(s['never_answered_pct'])} ({s['never_answered']})",
            "",
        ]
    if result["skipped_rows"]:
        lines.append(f"Skipped {len(result['skipped_rows'])} row(s) that could not be timed:")
        for item in result["skipped_rows"]:
            lines.append(f"  row {item['row']}: {item['reason']}")
    return "\n".join(lines).rstrip() + "\n"


def build_parser():
    parser = argparse.ArgumentParser(
        description="Measure time to first response from a CSV export of enquiries. "
                    "Reads only the file given. Contacts no one.")
    parser.add_argument("csv_file", help="CSV export with a header row, one row per enquiry")
    parser.add_argument("--created", required=True, help="name of the column holding the time the enquiry arrived")
    parser.add_argument("--responded", required=True,
                        help="name of the column holding the time of the first response (blank means never answered)")
    parser.add_argument("--hours", default=DEFAULT_HOURS,
                        help=f"working hours, for example 'Mon-Sat 08:00-18:00' (default: {DEFAULT_HOURS})")
    parser.add_argument("--timezone", default=DEFAULT_TZ,
                        help=f"timezone for times with no offset (default: {DEFAULT_TZ})")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON instead of text")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        rows = read_rows(args.csv_file, args.created, args.responded)
        result = analyse(rows, args.created, args.responded, args.hours, args.timezone)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ZoneInfoNotFoundError:
        print(f"error: unknown timezone {args.timezone!r}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render_text(result), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
