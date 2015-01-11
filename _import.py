# vim: set fileencoding=utf-8 :
import sqlalchemy
import re
import dateutil.parser
from datetime import timedelta, datetime


def normalizeMove(move):
    if move.ascentTime.total_seconds() == 0:
        assert move.ascent == 0
        move.ascent = None

    if move.descentTime.total_seconds() == 0:
        assert float(move.descent) == 0
        move.descent = None

    if move.activity == 'Outdoor swimmin':
        move.activity = 'Outdoor swimming'


def normalizeTag(tag, ns='http://www.suunto.com/schemas/sml'):
    return tag.replace("{%s}" % ns, "")


def _convertAttr(columnType, value, attr, message):
    if columnType == sqlalchemy.sql.sqltypes.Float:
        assert re.match(r"^\-?\d+(\.\d+)?$", value), message
        return float(value)
    elif columnType == sqlalchemy.sql.sqltypes.Interval:
        assert re.match(r"^\-?\d+(\.\d+)?$", value), message
        seconds = float(value)
        return timedelta(seconds=seconds)
    elif columnType == sqlalchemy.sql.sqltypes.Integer:
        if (value == "0"):
            return 0
        else:
            assert re.match(r"^\-?(\d+|0x[0-9A-F]+)$", value), message
            if re.match(r"^0x[0-9A-F]+$", value):
                return int(value, 16)
            else:
                return int(value, 10)

    elif columnType == sqlalchemy.sql.sqltypes.String:
        assert re.match(r"^[0-9a-zA-Z ,-.]+$", value), message
        return value
    elif columnType == sqlalchemy.sql.sqltypes.DateTime:
        assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$", value), message
        value = dateutil.parser.parse(value)
        assert isinstance(value, datetime)
        return value
    else:
        raise Exception("Unknown column type: %s for attribute '%s'" % (columnType, attr))


def setAttr(move, attr, value):
    assert hasattr(move, attr), "attribute '%s' not found" % attr
    old_value = getattr(move, attr)
    assert old_value is None, "value for '%s' already set'" % attr
    prop = getattr(type(move), attr).property
    assert len(prop.columns) == 1

    value = _convertAttr(type(prop.columns[0].type), value, attr, "illegal value '%s' for '%s'" % (value, attr))
    setattr(move, attr, value)


def addChildren(move, element):
    for child in element.iterchildren():
        tag = normalizeTag(child.tag)
        tag = tag[0].lower() + tag[1:]

        if tag == 'hR':
            tag = 'hr'

        if tag in ['speed', 'hr', 'cadence', 'temperature', 'altitude']:
            for subChild in child.iterchildren():
                subTag = tag + normalizeTag(subChild.tag)
                setAttr(move, subTag, value=subChild.text)
        else:
            setAttr(move, tag, value=child.text)


def _parseRecursive(node):
    if node.countchildren() > 0:
        events = {}
        for child in node.iterchildren():
            tag = normalizeTag(child.tag)
            if len(tag) > 2 and tag.upper() != tag:
                tag = tag[0].lower() + tag[1:]

            data = _parseRecursive(child)
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


def parseJson(node):
    return _parseRecursive(node)
