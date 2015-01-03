#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from initialize_config import initializeConfig
import re


class TestInitializeSchema(object):

    def test_initialize_schema(self, tmpdir):
        tmpfile = tmpdir.join("openmoves.cfg")
        initializeConfig(tmpfile)
        lines = tmpfile.readlines()
        assert len(lines) == 1
        assert re.match(r"SECRET_KEY = '[a-f0-9]{64}'", lines[0]), "unexpected line: %s" % lines[0]

    def test_initialize_schema_subsequent_calls_differ(self, tmpdir):

        tmpfile1 = tmpdir.join("openmoves1.cfg")
        tmpfile2 = tmpdir.join("openmoves2.cfg")
        initializeConfig(tmpfile1)
        initializeConfig(tmpfile2)

        assert tmpfile1.read() != tmpfile2.read()
