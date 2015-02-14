# vim: set fileencoding=utf-8 :
import sqlalchemy
import re
import dateutil.parser
from datetime import timedelta, datetime


def normalize_move(move):
    if move.ascent_time.total_seconds() == 0:
        assert move.ascent == 0
        move.ascent = None

    if move.descent_time.total_seconds() == 0:
        assert float(move.descent) == 0
        move.descent = None

    if move.activity == 'Outdoor swimmin':
        move.activity = 'Outdoor swimming'


def normalize_tag(tag, ns='http://www.suunto.com/schemas/sml', camel_case_to_underscores=True):
    normalized_tag = tag.replace("{%s}" % ns, '')
    if camel_case_to_underscores:
        # http://stackoverflow.com/a/1176023/4308
        normalized_tag = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', normalized_tag)
        normalized_tag = re.sub('([a-z0-9])([A-Z])', r'\1_\2', normalized_tag).lower()
    return normalized_tag


def _convert_attr(column_type, value, attr, message):
    if column_type == sqlalchemy.sql.sqltypes.Float:
        assert re.match(r"^\-?\d+(\.\d+)?$", value), message
        return float(value)
    elif column_type == sqlalchemy.sql.sqltypes.Interval:
        assert re.match(r"^\-?\d+(\.\d+)?$", value), message
        seconds = float(value)
        return timedelta(seconds=seconds)
    elif column_type == sqlalchemy.sql.sqltypes.Integer:
        if (value == "0"):
            return 0
        else:
            assert re.match(r"^\-?(\d+|0x[0-9A-F]+)$", value), message
            if re.match(r"^0x[0-9A-F]+$", value):
                return int(value, 16)
            else:
                return int(value, 10)

    elif column_type == sqlalchemy.sql.sqltypes.String:
        assert re.match(r"^[0-9a-zA-Z ,-.]+$", value), message
        return value
    elif column_type == sqlalchemy.sql.sqltypes.DateTime:
        assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$", value), message
        value = dateutil.parser.parse(value)
        assert isinstance(value, datetime)
        return value
    else:
        raise Exception("Unknown column type: %s for attribute '%s'" % (column_type, attr))


def set_attr(move, attr, value):
    assert hasattr(move, attr), "attribute '%s' not found" % attr
    old_value = getattr(move, attr)
    assert old_value is None, "value for '%s' already set'" % attr
    prop = getattr(type(move), attr).property
    assert len(prop.columns) == 1

    value = _convert_attr(type(prop.columns[0].type), value, attr, "illegal value '%s' for '%s'" % (value, attr))
    setattr(move, attr, value)


def add_children(move, element):
    for child in element.iterchildren():
        tag = normalize_tag(child.tag)

        if tag in ('speed', 'hr', 'cadence', 'temperature', 'altitude'):
            for sub_child in child.iterchildren():
                sub_tag = tag + '_' + normalize_tag(sub_child.tag)
                set_attr(move, sub_tag, value=sub_child.text)
        else:
            set_attr(move, tag, value=child.text)


def _parse_recursive(node):
    if node.countchildren() > 0:
        events = {}
        for child in node.iterchildren():
            tag = normalize_tag(child.tag, camel_case_to_underscores=False)
            if len(tag) > 2 and tag.upper() != tag:
                tag = tag[0].lower() + tag[1:]

            data = _parse_recursive(child)
            if tag in events:
                if not isinstance(events[tag], list):
                    events[tag] = [events[tag]]
                events[tag].append(data)
            else:
                events[tag] = data
        return events
    else:
        if len(node.text) > 0:
            return node.text
        else:
            return None


def parse_json(node):
    return _parse_recursive(node)
