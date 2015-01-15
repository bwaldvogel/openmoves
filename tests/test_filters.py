# vim: set fileencoding=utf-8 :

import filters
from datetime import timedelta


class TestFilters(object):

    def test_duration(self):
        assert filters.duration('127.12') == "00:02:07.12"
        assert filters.duration(u'127.12') == "00:02:07.12"
        assert filters.duration(127.12) == "00:02:07.12"
        assert filters.duration(127) == "00:02:07.00"
        assert filters.duration(timedelta(seconds=127)) == "00:02:07.00"
