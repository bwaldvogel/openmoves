[![Build Status](https://travis-ci.org/bwaldvogel/openmoves.png?branch=master)](https://travis-ci.org/bwaldvogel/openmoves)

# OpenMoves #
An open source alternative to Movescount.

## Key features ##
 - Free and open-source software
 - OpenStreetMap integration
 - Plots with curve smoothing and outlier detection

## Requirements ##
 - Python 2.7, 3.3 or 3.4
 - [virtualenv][virtualenv]
 - [pip (package manager)][pip]

## Setup ##

```
# virtualenv virtualenv
# source virtualenv/bin/activate
# pip install -r requirements.txt
# ./webapp.py create-schema
# ./webapp.py add-user -u <your_username>
```

## Running ##
```
# ./webapp.py runserver
* Running on http://127.0.0.1:5000/
```

Open [`http://127.0.0.1:5000/`][localhost5000] in your browser.

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

Then create the database schema and an user with
```
# ./webapp.py create-schema
# ./webapp.py add-user -u <your_username>
```


[pip]: http://en.wikipedia.org/wiki/Pip_%28package_manager%29
[virtualenv]: https://virtualenv.readthedocs.org/en/latest/
[localhost5000]: http://127.0.0.1:5000/
[openmoves.wsgi]: https://github.com/bwaldvogel/openmoves/blob/master/openmoves.wsgi
[modwsgi]: https://code.google.com/p/modwsgi/
