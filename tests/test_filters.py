# vim: set fileencoding=utf-8 :

from datetime import timedelta

import pytest

import filters


class TestFilters(object):

    def test_duration(self):
        assert filters.duration('127.12') == "00:02:07.12"
        assert filters.duration('127.12') == "00:02:07.12"
        assert filters.duration(127.12) == "00:02:07.12"
        assert filters.duration(127) == "00:02:07.00"
        assert filters.duration(timedelta(seconds=127)) == "00:02:07.00"

    def test_pace_km(self):
        assert filters.format_pace_km(10.0 / 3.6) == "06:00 min/km"
        assert filters.format_pace_km(12.0 / 3.6) == "05:00 min/km"
        assert filters.format_pace_km(14.5 / 3.6) == "04:08 min/km"

    def test_swim_pace(self):
        assert filters.swim_pace(timedelta(seconds=12.3456)) == "20:34.56 min / 100 m"

    def test_swim_pace_illegal_value(self):
        with pytest.raises(AssertionError):
            filters.swim_pace(1)

    def test_swim_pace_value_too_large(self):
        with pytest.raises(AssertionError):
            filters.swim_pace(timedelta(seconds=999))

    def test_get_city(self):
        address = {}
        assert filters.get_city(address) == None

        address['village'] = 'some village'
        assert filters.get_city(address) == 'some village'

        address['town'] = 'some town'
        assert filters.get_city(address) == 'some town'

        address['city_district'] = 'some city district'
        assert filters.get_city(address) == 'some city district'

        address['city'] = 'some city'
        assert filters.get_city(address) == 'some city'

    def test_short_location(self):
        location = {'address': {'city': 'some city', 'country_code': 'de'}}
        assert filters.short_location(location) == 'some city, DE'

        location = {'address': {'country': 'Germany'}}
        assert filters.short_location(location) == 'Germany'

        location = {}
        assert filters.short_location(location) == None
