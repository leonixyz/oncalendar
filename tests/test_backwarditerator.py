from __future__ import annotations

import unittest
from datetime import datetime
from itertools import product
from zoneinfo import ZoneInfo

from oncalendar import BackwardIterator, OnCalendarError

NOW = datetime(2020, 1, 1)


class TestParse(unittest.TestCase):
    def assert_default(self, w, fields):
        if "w" in fields:
            self.assertEqual(w.weekdays, set(range(0, 7)))
        if "y" in fields:
            self.assertEqual(w.years, set(range(1970, 2200)))
        if "m" in fields:
            self.assertEqual(w.months, set(range(1, 13)))
        if "d" in fields:
            self.assertEqual(w.days, set(range(1, 32)))
        if "H" in fields:
            self.assertEqual(w.hours, {0})
        if "M" in fields:
            self.assertEqual(w.minutes, {0})
        if "S" in fields:
            self.assertEqual(w.seconds, {0})

    def test_it_parses_stars(self) -> None:
        w = BackwardIterator("*-*-* *:*:*", NOW)
        self.assert_default(w, "wymd")
        self.assertEqual(w.hours, set(range(0, 24)))
        self.assertEqual(w.minutes, set(range(0, 60)))
        self.assertEqual(w.seconds, set(range(0, 60)))

    def test_it_parses_weekday(self) -> None:
        for sample in ("Mon", "MON", "Monday", "MONDAY"):
            w = BackwardIterator(sample, NOW)
            self.assert_default(w, "ymdHMS")
            self.assertEqual(w.weekdays, {0})

    def test_it_parses_weekday_with_trailing_comma(self) -> None:
        w = BackwardIterator("Mon, 12:34", NOW)
        self.assert_default(w, "ymdS")
        self.assertEqual(w.weekdays, {0})
        self.assertEqual(w.hours, {12})
        self.assertEqual(w.minutes, {34})

    def test_it_parses_weekday_interval(self) -> None:
        for sample in ("Mon..Tue", "Mon,Tue", "Mon-Tue"):
            w = BackwardIterator(sample, NOW)
            self.assert_default(w, "ymdHMS")
            self.assertEqual(w.weekdays, {0, 1})

    def test_it_parses_date(self) -> None:
        w = BackwardIterator("2023-11-30", NOW)
        self.assert_default(w, "wHMS")
        self.assertEqual(w.years, {2023})
        self.assertEqual(w.months, {11})
        self.assertEqual(w.days, {30})

    def test_it_handles_omitted_year(self) -> None:
        w = BackwardIterator("11-30", NOW)
        self.assert_default(w, "wyHMS")
        self.assertEqual(w.months, {11})
        self.assertEqual(w.days, {30})

    def test_it_handles_two_digit_year(self) -> None:
        w = BackwardIterator("69-*-*", NOW)
        self.assert_default(w, "wmdHMS")
        self.assertEqual(w.years, {2069})

    def test_it_handles_prev_century_two_digit_year(self) -> None:
        w = BackwardIterator("70-*-*", NOW)
        self.assert_default(w, "wmdHMS")
        self.assertEqual(w.years, {1970})

    def test_it_parses_time(self) -> None:
        w = BackwardIterator("11:22:33", NOW)
        self.assert_default(w, "wymd")
        self.assertEqual(w.hours, {11})
        self.assertEqual(w.minutes, {22})
        self.assertEqual(w.seconds, {33})

    def test_it_handles_omitted_seconds(self) -> None:
        w = BackwardIterator("11:22", NOW)
        self.assert_default(w, "wymdS")
        self.assertEqual(w.hours, {11})
        self.assertEqual(w.minutes, {22})

    def test_it_parses_list(self) -> None:
        w = BackwardIterator("*:1,2,3", NOW)
        self.assertEqual(w.minutes, {1, 2, 3})

    def test_it_parses_interval(self) -> None:
        w = BackwardIterator("*:1..3", NOW)
        self.assertEqual(w.minutes, {1, 2, 3})

    def test_it_parses_two_intervals(self) -> None:
        w = BackwardIterator("*:1..3,7..9:*", NOW)
        self.assertEqual(w.minutes, {1, 2, 3, 7, 8, 9})

    def test_it_parses_step(self) -> None:
        w = BackwardIterator("*:0/15", NOW)
        self.assertEqual(w.minutes, {0, 15, 30, 45})

    def test_it_parses_interval_with_step(self) -> None:
        w = BackwardIterator("*:0..10/2", NOW)
        self.assertEqual(w.minutes, {0, 2, 4, 6, 8, 10})

    def test_it_parses_start_with_step(self) -> None:
        w = BackwardIterator("*:5/15", NOW)
        self.assertEqual(w.minutes, {5, 20, 35, 50})

    def test_it_parses_negative_day(self) -> None:
        w = BackwardIterator("*-*~1", NOW)
        self.assertEqual(w.days, {-1})

    def test_it_parses_negative_day_sans_year(self) -> None:
        w = BackwardIterator("*~1", NOW)
        self.assertEqual(w.days, {-1})

    def test_it_parses_negative_day_list(self) -> None:
        w = BackwardIterator("*-*~1,8", NOW)
        self.assertEqual(w.days, {-1, -8})

    def test_it_parses_negative_day_interval(self) -> None:
        w = BackwardIterator("*-*~1..3", NOW)
        self.assertEqual(w.days, {-1, -2, -3})

    def test_it_parses_two_negative_day_intervals(self) -> None:
        w = BackwardIterator("*-*~1..2,4..5", NOW)
        self.assertEqual(w.days, {-1, -2, -4, -5})

    def test_it_parses_negative_day_interval_with_step(self) -> None:
        w = BackwardIterator("*-*~1..5/2", NOW)
        self.assertEqual(w.days, {-1, -3, -5})

    def test_it_parses_negative_day_start_with_step(self) -> None:
        w = BackwardIterator("*-*~3/2", NOW)
        self.assertEqual(w.days, {-1, -3})

    def test_it_parses_special_expression(self) -> None:
        for sample in ("minutely", "Minutely", "MINUTELY", "MiNuTeLY"):
            w = BackwardIterator(sample, NOW)
            self.assert_default(w, "wymd")
            self.assertEqual(w.hours, set(range(0, 24)))
            self.assertEqual(w.minutes, set(range(0, 60)))
            self.assertEqual(w.seconds, {0})


class TestValidation(unittest.TestCase):
    def test_it_rejects_empty_string(self) -> None:
        with self.assertRaisesRegex(OnCalendarError, "Wrong number of fields"):
            BackwardIterator("", NOW)

    def test_it_rejects_4_components(self) -> None:
        with self.assertRaisesRegex(OnCalendarError, "Wrong number of fields"):
            BackwardIterator("Mon *-*-* *:*:* surprise", NOW)

    def test_it_rejects_bad_values(self) -> None:
        patterns = (
            "%s *-*-* *:*:*",
            "%s-*-*",
            "*-%s-*",
            "*-*-%s",
            "*-*~%s",
            "%s:*:*",
            "*:%s:*",
            "*:*:%s",
        )

        bad_values = (
            "-1",
            "1000",
            "ABC",
            "1-1",
            "1:1",
            "Mon/1",
            "~1",
            "*/1",
            "*,1",
            "1..*",
        )

        for pattern, s in product(patterns, bad_values):
            with self.assertRaises(OnCalendarError):
                BackwardIterator(pattern % s, NOW)

    def test_it_rejects_lopsided_range(self) -> None:
        with self.assertRaisesRegex(OnCalendarError, "Bad day-of-month"):
            BackwardIterator("*-*-5..1", NOW)

    def test_it_rejects_underscores(self) -> None:
        with self.assertRaisesRegex(OnCalendarError, "Bad minute"):
            BackwardIterator("*:1..1_0", NOW)

    def test_it_rejects_zero_step(self) -> None:
        with self.assertRaisesRegex(OnCalendarError, "Bad minute"):
            BackwardIterator("*:*/0", NOW)

    def test_it_checks_day_of_month_range(self) -> None:
        with self.assertRaisesRegex(OnCalendarError, "Bad day-of-month"):
            BackwardIterator("1-32", NOW)

    def test_it_rejects_weekday_star(self) -> None:
        with self.assertRaisesRegex(OnCalendarError, "Bad day-of-week"):
            BackwardIterator("* 1-1", NOW)

    def test_it_rejects_reverse_dom_above_28(self) -> None:
        with self.assertRaisesRegex(OnCalendarError, "Bad day-of-month"):
            BackwardIterator("1~29", NOW)


class TestIterator(unittest.TestCase):
    def test_it_works_as_iterator(self) -> None:
        hits = list(BackwardIterator("2019-01-01 8..9:0:0", NOW))
        self.assertEqual(len(hits), 2)
        self.assertEqual(hits[0].isoformat(), "2019-01-01T09:00:00")
        self.assertEqual(hits[1].isoformat(), "2019-01-01T08:00:00")

    def test_it_handles_every_5th_second(self) -> None:
        it = BackwardIterator("*:*:0/5", NOW)
        self.assertEqual(next(it).isoformat(), "2019-12-31T23:59:55")
        self.assertEqual(next(it).isoformat(), "2019-12-31T23:59:50")

    def test_it_handles_every_minute(self) -> None:
        it = BackwardIterator("*:*", NOW)
        self.assertEqual(next(it).isoformat(), "2019-12-31T23:59:00")
        self.assertEqual(next(it).isoformat(), "2019-12-31T23:58:00")

    def test_it_handles_every_feb_29_monday(self) -> None:
        it = BackwardIterator("Mon 2-29", NOW)
        self.assertEqual(next(it).isoformat(), "2016-02-29T00:00:00")
        self.assertEqual(next(it).isoformat(), "1988-02-29T00:00:00")

    def test_it_handles_every_last_day_of_month(self) -> None:
        it = BackwardIterator("*~1", NOW)
        self.assertEqual(next(it).isoformat(), "2019-12-31T00:00:00")
        self.assertEqual(next(it).isoformat(), "2019-11-30T00:00:00")
        self.assertEqual(next(it).isoformat(), "2019-10-31T00:00:00")

    def test_it_handles_last_sunday_of_every_month(self) -> None:
        it = BackwardIterator("Sun *~7/1", NOW)
        self.assertEqual(next(it).isoformat(), "2019-12-29T00:00:00")
        self.assertEqual(next(it).isoformat(), "2019-11-24T00:00:00")
        self.assertEqual(next(it).isoformat(), "2019-10-27T00:00:00")

    def test_it_handles_no_occurences(self) -> None:
        it = BackwardIterator("2021-01-01", NOW)
        with self.assertRaises(StopIteration):
            print(next(it))

    def test_it_handles_midnight(self) -> None:
        it = BackwardIterator("00:00", NOW)
        self.assertEqual(next(it).isoformat(), "2019-12-31T00:00:00")


class TestDstHandling(unittest.TestCase):
    tz = ZoneInfo("Europe/Riga")

    def test_it_preserves_timezone(self) -> None:
        now = datetime(2020, 1, 1, tzinfo=self.tz)

        it = BackwardIterator("*:*", now)
        self.assertEqual(next(it).isoformat(), "2019-12-31T23:59:00+02:00")
        self.assertEqual(next(it).isoformat(), "2019-12-31T23:58:00+02:00")

    def test_it_handles_spring_dst(self) -> None:
        now = datetime(2020, 5, 1, tzinfo=self.tz)

        it = BackwardIterator("*-*-29 3:30", now)
        self.assertEqual(next(it).isoformat(), "2020-04-29T03:30:00+03:00")
        self.assertEqual(next(it).isoformat(), "2020-02-29T03:30:00+02:00")
        self.assertEqual(next(it).isoformat(), "2020-01-29T03:30:00+02:00")

    def test_it_handles_autumn_dst(self) -> None:
        now = datetime(2020, 12, 31, tzinfo=self.tz)

        it = BackwardIterator("*-*-25 3:30", now)
        self.assertEqual(next(it).isoformat(), "2020-12-25T03:30:00+02:00")
        self.assertEqual(next(it).isoformat(), "2020-11-25T03:30:00+02:00")
        self.assertEqual(next(it).isoformat(), "2020-10-25T03:30:00+03:00")


if __name__ == "__main__":
    unittest.main()
