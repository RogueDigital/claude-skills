import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import lead_timing  # noqa: E402

FIXTURES = HERE / "fixtures"


def run(name, *extra, created="created", responded="first_response"):
    """Run the script on a fixture. Returns (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    argv = [str(FIXTURES / name), "--created", created, "--responded", responded, *extra]
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = lead_timing.main(argv)
    return code, out.getvalue(), err.getvalue()


def stats(name, *extra, **kwargs):
    code, out, err = run(name, "--json", *extra, **kwargs)
    assert code == 0, err
    return json.loads(out)


class InputErrors(unittest.TestCase):
    def test_empty_file(self):
        code, out, err = run("empty.csv")
        self.assertEqual(code, 2)
        self.assertIn("empty", err)

    def test_missing_column_names_the_columns_found(self):
        code, out, err = run("missing_column.csv")
        self.assertEqual(code, 2)
        self.assertIn("first_response", err)
        self.assertIn("replied_at", err)

    def test_missing_file(self):
        code, out, err = run("does_not_exist.csv")
        self.assertEqual(code, 2)
        self.assertIn("not found", err)

    def test_bad_hours(self):
        code, out, err = run("uk_format.csv", "--hours", "whenever")
        self.assertEqual(code, 2)
        self.assertIn("working hours", err)

    def test_unknown_timezone(self):
        code, out, err = run("uk_format.csv", "--timezone", "Mars/Olympus")
        self.assertEqual(code, 2)
        self.assertIn("timezone", err)

    def test_header_only_has_no_enquiries(self):
        result = stats("header_only.csv")
        self.assertEqual(result["overall"]["count"], 0)
        self.assertIsNone(result["overall"]["median_minutes"])
        code, out, err = run("header_only.csv")
        self.assertEqual(code, 0)
        self.assertIn("none", out)


class DateFormats(unittest.TestCase):
    def test_uk_format(self):
        s = stats("uk_format.csv")["overall"]
        self.assertEqual(s["count"], 2)
        self.assertEqual(s["median_minutes"], 46.5)  # median of 3 and 90

    def test_iso_formats_including_offsets(self):
        s = stats("iso_format.csv")["overall"]
        self.assertEqual(s["count"], 3)
        # 3 min, 90 min, and 10 min (March is GMT, so Z and local agree)
        self.assertEqual(s["median_minutes"], 10)
        self.assertEqual(s["within_5_min_pct"], 33.3)
        self.assertEqual(s["within_1_hour_pct"], 66.7)

    def test_semicolon_delimiter_and_bom_and_case_insensitive_columns(self):
        result = stats("semicolon_bom.csv", created="created", responded="first reply")
        self.assertEqual(result["overall"]["median_minutes"], 10)

    def test_parse_time_rejects_date_only(self):
        tz = lead_timing.ZoneInfo("Europe/London")
        self.assertIsNone(lead_timing.parse_time("10/03/2026", tz))
        self.assertIsNone(lead_timing.parse_time("2026-03-10", tz))


class NeverAnswered(unittest.TestCase):
    def test_blank_response_counts_as_never_answered(self):
        s = stats("never_answered.csv")["overall"]
        self.assertEqual(s["count"], 4)
        self.assertEqual(s["answered"], 2)
        self.assertEqual(s["never_answered"], 2)
        self.assertEqual(s["never_answered_pct"], 50.0)
        # Shares are of all enquiries: one of four answered in 5 minutes.
        self.assertEqual(s["within_5_min_pct"], 25.0)
        self.assertEqual(s["within_1_hour_pct"], 50.0)
        self.assertEqual(s["median_minutes"], 27.0)  # median of 4 and 50
        self.assertEqual(s["same_working_day_pct"], 50.0)


class Weekends(unittest.TestCase):
    def test_weekend_enquiries_are_out_of_hours_and_use_next_working_day(self):
        result = stats("weekend.csv")
        self.assertEqual(result["in_hours"]["count"], 0)
        s = result["out_of_hours"]
        self.assertEqual(s["count"], 3)
        # Fri 18:42 to Mon 09:20 is 62h38m, Sat 11:00 to Mon 16:00 is 53h,
        # Sat 12:00 to Tue 09:00 is 69h.
        self.assertEqual(s["median_minutes"], 3758)
        # Two were answered by close of Monday. The third waited until Tuesday.
        self.assertEqual(s["same_working_day_pct"], 66.7)

    def test_saturday_working_changes_the_split(self):
        result = stats("weekend.csv", "--hours", "Mon-Sat 09:00-13:00")
        # Saturday 11:00 is now in hours, Saturday 12:00 too, Friday 18:42 is not.
        self.assertEqual(result["in_hours"]["count"], 2)
        self.assertEqual(result["out_of_hours"]["count"], 1)

    def test_deadline_rules(self):
        tz = lead_timing.ZoneInfo("Europe/London")
        hours = lead_timing.parse_hours("Mon-Fri 09:00-17:30")
        wed_morning = lead_timing.parse_time("2026-03-11 07:00", tz)
        wed_noon = lead_timing.parse_time("2026-03-11 12:00", tz)
        fri_evening = lead_timing.parse_time("2026-03-06 18:00", tz)
        close = lead_timing.same_working_day_deadline
        self.assertEqual(close(wed_morning, hours, tz).strftime("%d %H:%M"), "11 17:30")
        self.assertEqual(close(wed_noon, hours, tz).strftime("%d %H:%M"), "11 17:30")
        self.assertEqual(close(fri_evening, hours, tz).strftime("%d %H:%M"), "09 17:30")


class ClockChanges(unittest.TestCase):
    def test_elapsed_time_is_real_time_across_bst_and_gmt(self):
        s = stats("clock_change.csv")["overall"]
        # 25 Oct 2026, 00:30 BST to 03:30 GMT: the clocks went back, so 4 hours.
        # 28 Mar 2026, 23:30 GMT to 03:30 BST: the clocks went forward, so 3 hours.
        self.assertEqual(s["median_minutes"], 210)
        self.assertEqual(s["p90_minutes"], 234.0)

    def test_offset_times_convert_to_local(self):
        tz = lead_timing.ZoneInfo("Europe/London")
        moment = lead_timing.parse_time("2026-07-01T12:00:00Z", tz)
        self.assertEqual(moment.hour, 13)  # BST


class BadRows(unittest.TestCase):
    def test_unusable_rows_are_skipped_and_reported(self):
        result = stats("bad_rows.csv")
        self.assertEqual(result["overall"]["count"], 2)
        reasons = {item["row"]: item["reason"] for item in result["skipped_rows"]}
        self.assertEqual(sorted(reasons), [3, 4, 5, 6])
        self.assertIn("not a date", reasons[3])
        self.assertIn("first response time", reasons[4])
        self.assertIn("before", reasons[5])
        text = run("bad_rows.csv")[1]
        self.assertIn("Skipped 4 row(s)", text)


class Maths(unittest.TestCase):
    def test_percentile(self):
        self.assertEqual(lead_timing.percentile([5], 90), 5)
        self.assertEqual(lead_timing.percentile([0, 10], 90), 9)
        self.assertEqual(lead_timing.percentile(list(range(1, 12)), 90), 10)

    def test_parse_hours(self):
        days, opens, closes = lead_timing.parse_hours("Mon,Wed,Fri 8:00-12:30")
        self.assertEqual(days, {0, 2, 4})
        self.assertEqual((opens.hour, closes.minute), (8, 30))
        with self.assertRaises(lead_timing.InputError):
            lead_timing.parse_hours("Mon-Fri 17:00-09:00")


if __name__ == "__main__":
    unittest.main()
