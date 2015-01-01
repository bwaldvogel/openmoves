#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import os
import os.path
import sys

filename = 'openmoves.cfg'

if os.path.isfile(filename):
    print("'%s' already exists" % filename)
    sys.exit(1)

random_bytes = os.urandom(32)

if isinstance(random_bytes[0], str):
    random_bytes = [ord(c) for c in random_bytes]

data = "SECRET_KEY = '%s'\n" % "".join("{:02x}".format(c) for c in random_bytes)
with open(filename, 'w') as f:
    f.write(data)

print("created %s" % filename)
