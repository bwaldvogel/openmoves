#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import os
import os.path

filename = 'openmoves.cfg'

assert not os.path.isfile(filename), "%s already exists" % filename

random_bytes = os.urandom(32)
data = "SECRET_KEY = '%s'\n" % "".join([hex(c)[2:] for c in random_bytes])
with open(filename, 'w') as f:
    f.write(data)
