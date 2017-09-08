[![Build Status](https://travis-ci.org/bwaldvogel/openmoves.png?branch=master)](https://travis-ci.org/bwaldvogel/openmoves)
[![MIT License](https://img.shields.io/github/license/bwaldvogel/openmoves.svg)](https://opensource.org/licenses/MIT)

# OpenMoves #
An open source alternative to Movescount.


## Key features ##
 - Free and open-source software
 - OpenStreetMap integration
 - Plots with curve smoothing


## Requirements ##
 - Python 2.7, 3.4, 3.5 or 3.6
 - [virtualenv][virtualenv]
 - [pip (package manager)][pip]


## Setup ##

```
# cp openmoves.cfg.default openmoves.cfg
# virtualenv virtualenv
# source virtualenv/bin/activate
# pip install -r requirements.txt
# ./openmoves.py add-user -u <your_username> [-p <your_password]
```

## Configuration

Configurations and parameters of `openmoves.cfg`

Required:
* __SQLALCHEMY_DATABASE_URI__ Database URL to be used

Optional:
* __BING_MAPS_API_KEY__ Bing maps API key. If not configured the Bing maps layers are disabled. Get your own key at https://www.bingmapsportal.com
* __STRAVA_CLIENT_ID__ The client ID of the [Strava application][strava-application] (example: `12345`)
* __STRAVA_CLIENT_SECRET__ The client secret of the [Strava application][strava-application] (example: `'ea01c8e942fd68a98d47ad96adb936a564089e2e'`)


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

Hints or pull requests how to automate the qunit tests are welcome.


## Deployment ##

We ship the [`openmoves.wsgi`][openmoves.wsgi] script to deploy OpenMoves in a Apache HTTP server with [`mod_wsgi`][modwsgi].

Example configuration
```
<VirtualHost 127.0.0.1:80>
    ServerAlias your.domain
    ServerName your.domain

    DocumentRoot /var/www/openmoves

    AddDefaultCharset utf-8

    WSGIDaemonProcess openmoves user=openmoves group=openmoves processes=1 threads=5 python-home=/var/www/openmoves/virtualenv python-path=/var/www/openmoves lang='en_US.UTF-8' locale='en_US.UTF-8'
    WSGIScriptAlias   / /var/www/openmoves/openmoves.wsgi

    <Directory /var/www/openmoves>
        WSGIProcessGroup openmoves
        WSGIApplicationGroup %{GLOBAL}
        Order deny,allow
        Allow from all
    </Directory>

    ServerAdmin mail@your.domain
</VirtualHost>
```

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
[strava-application]: https://www.strava.com/settings/api
