[![Build Status](https://travis-ci.org/bwaldvogel/openmoves.png?branch=master)](https://travis-ci.org/bwaldvogel/openmoves)

# OpenMoves #
An open source alternative to Movescount.


## Key features ##
 - Free and open-source software
 - OpenStreetMap integration
 - Plots with curve smoothing


## Requirements ##
 - Python 2.7, 3.3 or 3.4
 - [virtualenv][virtualenv]
 - [pip (package manager)][pip]


## Setup ##

```
# virtualenv virtualenv
# source virtualenv/bin/activate
# pip install -r requirements.txt
# ./openmoves.py add-user -u <your_username>
```


## Running ##
```
# ./openmoves.py runserver
* Running on http://127.0.0.1:5000/
```

Open [`http://127.0.0.1:5000/`](http://127.0.0.1:5000/) in your browser.


## Testing ##

We use [`py.test`][pytest] to test server side code. Tests are executed with the following command given that your [virtualenv][virtualenv] is activated:
```
# py.test
```

If a test fails it might help to run in verbose mode and stop on the first failure:
```
# py.test -vsx
```

Note that the majority of unit tests write the latest HTML response to a local tempfile in `/tmp/pytest-<your-username>/response.html` using [py.test's `tmpdir` mechansism][pytest-tmpdir].

JavaScript unit tests are written with [QUnit][qunit] and are not yet automated in the build and need to be run in a browser by browsing to:

[`http://127.0.0.1:5000/_tests`](http://127.0.0.1/_tests)

Hints or pull requests how to automate the qunit tests it are welcome.


## Deployment ##

We ship the [`openmoves.wsgi`][openmoves.wsgi] script to deploy OpenMoves in a Apache HTTP server with [`mod_wsgi`][modwsgi].

### PostgreSQL ###

While OpenMoves uses an on-disk SQLite database by default, we recommend to
deploy OpenMoves on a proper database such as PostgreSQL.

First create a database and login role.
Then overwrite the openmoves default database url in the `openmoves.cfg` file:

```
SQLALCHEMY_DATABASE_URI = 'postgresql://<user>:<password>@localhost:5432/<database>'
```

Then create/upgrade the database schema with:
```
# ./openmoves.py db upgrade
```

Create an initial user:
```
# ./openmoves.py add-user -u <your_username>
```


[pip]: http://en.wikipedia.org/wiki/Pip_%28package_manager%29
[virtualenv]: https://virtualenv.readthedocs.org/en/latest/
[openmoves.wsgi]: https://github.com/bwaldvogel/openmoves/blob/master/openmoves.wsgi
[modwsgi]: https://code.google.com/p/modwsgi/
[pytest]: https://pytest.org/
[pytest-tmpdir]: https://pytest.org/latest/tmpdir.html
[qunit]: https://qunitjs.com/
