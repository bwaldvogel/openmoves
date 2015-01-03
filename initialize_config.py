#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import os
import os.path
import sys


def initializeConfig(f):

    random_bytes = os.urandom(32)

    if isinstance(random_bytes[0], str):
        random_bytes = [ord(c) for c in random_bytes]

    data = "SECRET_KEY = '%s'\n" % "".join("{:02x}".format(c) for c in random_bytes)
    f.write(data)


if __name__ == "__main__":
    filename = 'openmoves.cfg'

    if os.path.isfile(filename):
        print("'%s' already exists" % filename)
        sys.exit(1)

    with open(filename, 'w') as f:
        initializeConfig(f)

    print("created %s" % filename)
