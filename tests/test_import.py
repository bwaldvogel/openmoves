# vim: set fileencoding=utf-8 :

from _import import normalize_tag


class TestImport(object):

    def test_normalize_tag(self):
        assert normalize_tag('{http://www.suunto.com/schemas/sml}SwimPace') == 'swim_pace'
        assert normalize_tag('ascentTime') == 'ascent_time'
        assert normalize_tag('TheAvgMove') == 'the_avg_move'
        assert normalize_tag('move_time') == 'move_time'
        assert normalize_tag('gpsHDOP') == 'gps_hdop'
