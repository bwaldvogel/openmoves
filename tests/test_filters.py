# vim: set fileencoding=utf-8 :

import filters
from datetime import timedelta
import pytest


class TestFilters(object):

    def test_duration(self):
        assert filters.duration('127.12') == "00:02:07.12"
        assert filters.duration(u'127.12') == "00:02:07.12"
        assert filters.duration(127.12) == "00:02:07.12"
        assert filters.duration(127) == "00:02:07.00"
        assert filters.duration(timedelta(seconds=127)) == "00:02:07.00"

    def test_swim_pace(self):
        assert filters.swim_pace(timedelta(seconds=12.3456)) == "20:34.56 min / 100 m"

    def test_swim_pace_illegal_value(self):
        with pytest.raises(AssertionError):
            filters.swim_pace(1)

    def test_swim_pace_value_too_large(self):
        with pytest.raises(AssertionError):
            filters.swim_pace(timedelta(seconds=999))