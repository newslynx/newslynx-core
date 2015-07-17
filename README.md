# newslynx

**This is still a WIP and we should be officially open-sourcing the codebase in late June/July 2015. For now, please read [the report](http://towcenter.org/research/the-newslynx-impact-tracker-produced-these-key-ideas/) we published for the [TowCenter](http://towcenter.org) on our prototype.**
 

## (Re)Setting up the dev environment

#### Install `newslynx`, prefrerably in a virtual environment.

```
git clone https://github.com/newslynx/newslynx.git
cd newslynx
python setup.py install
```

If you want to actively work on the codebase, install in `editable` mode:

```
git clone https://github.com/newslynx/newslynx.git
cd newslynx
pip install --editable . 
```

#### Install the dependencies (instructions for Mac OS X, for now):

Install `redis`:

```
brew install redis
```

**NOTE** We recommend using [Postgres APP](http://postgresapp.com/). However, if you prefer the `brew` distribution, make sure to install it with plpythonu.

```
brew install postgresql --build-from-source --with-python
```

(Re)create a `postgresql` database

```
dropdb newslynx 
createdb newslynx
```

#### Set your configurations

- fill out [`example_config/config.yaml`](example_config/config.yaml) and move it to `~/.newslynx/config.yaml`
- follow the [SQLAlchemy Docs](http://docs.sqlalchemy.org/en/rel_1_0/core/engines.html#database-urls) for details on how to configure your `sqlalchemy_database_uri`.
- Modify default recipes and tags in [`example_config/defaults/recipes.yaml`](example_config/defaults/recipes.yaml) and [`example_config/defaults/tags.yaml`](example_config/defaults/tags.yaml). These tags and recipes will be created everytime a new organization is added. If you'd simply like to use our defaults, type `make defaults`. This will move these files to `~/.newslynx/defaults`.

#### Start the redis server

Open another shell and run:

```
redis-server
```

#### Initialize the database, super user, and instlall built-in sous chefs.

```
newslynx init
```

#### Start the server

- In debug mode: `newslynx debug`
- Debug mode with errors: `newslynx debug --raise-errors`
- Production `guniorn` server: `./run`

#### Start the task workers

```
./start_workers
```
stop the tasks workers
```
./stop_workers
```

#### Start the cron daemon
```
newslynx cron
```

#### IGNORE THIS ERROR:

This is a result of our extensive use of `gevent`. We haven't yet figured out how to properly suppress this error. See more details [here](http://stackoverflow.com/questions/8774958/keyerror-in-module-threading-after-a-successful-py-test-run).

```
Exception KeyError: KeyError(4332017936,) in <module 'threading' from '/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/threading.pyc'> ignored
```

## TODO 
- [ ] Fix Bulk Loading process.
- [ ] Re-implement SousChefs
    - [x] RSS Feeds => Thing
    - [x] Google Analytics => Metric
    - [ ] Google Alerts => Event
    - [x] Social Shares => Metric
    - [ ] Homepage Promotions => Metric
    - [x] Twitter Promotions => Metric
    - [ ] Facebook Promotions => Metric
    - [x] Twitter List => Event 
    - [x] Twitter User => Event 
    - [ ] Facebook Page => Event 
    - [x] Reddit => Event
    - [ ] HackerNews => Event
- [ ] Implement New SousChefs 
    - [ ] IFTTT integrations
        - [ ] Wordpress Publish => Thing
        - TK
    - [ ] Regex Thing URL => Tag 
    - [ ] Search Things => Tag 
    - [ ] Meltwater Emails => Event
    - [ ] Newsletter Email Promotions => Metric
    - [ ] Calculated Metric? SQL API.
- [x] Implement Recipe scheduler
- [ ] Implement Admin Panel
- [ ] Migrate Core Prototype Users.
- [ ] Automate Deployment
- [ ] App Integration
- [ ] Document, Document, Document

## References

#### API Design

* [http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api](http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api)

#### Crosstab in Postgres
* [http://www.postgresonline.com/journal/archives/14-CrossTab-Queries-in-PostgreSQL-using-tablefunc-contrib.html](http://www.postgresonline.com/journal/archives/14-CrossTab-Queries-in-PostgreSQL-using-tablefunc-contrib.html)

#### filling in zeros for a timezeries
* [http://stackoverflow.com/questions/346132/postgres-how-to-return-rows-with-0-count-for-missing-data]

#### fetching column names from table
* [http://www.postgresql.org/message-id/AANLkTilsjTAXyN5DghR3M2U4c8w48UVxhov4-8igMpd1@mail.gmail.com](http://www.postgresql.org/message-id/AANLkTilsjTAXyN5DghR3M2U4c8w48UVxhov4-8igMpd1@mail.gmail.com)

#### timeseries tips
* [http://no0p.github.io/postgresql/2014/05/08/timeseries-tips-pg.html](http://no0p.github.io/postgresql/2014/05/08/timeseries-tips-pg.html)

#### Getting bigger with flask (+ dynamic subdomains):
* [http://maximebf.com/blog/2012/11/getting-bigger-with-flask/#.VVYvUZNVhBc](http://maximebf.com/blog/2012/11/getting-bigger-with-flask/#.VVYvUZNVhBc)

#### Nonblocking with flask, gevent, + psycopg2
* [https://github.com/kljensen/async-flask-sqlalchemy-example](https://github.com/kljensen/async-flask-sqlalchemy-example)

#### Rate Limiting in Flask.
* [http://flask.pocoo.org/snippets/70/](http://flask.pocoo.org/snippets/70/)

#### Postgres Search Configuration
* [http://sqlalchemy-searchable.readthedocs.org/en/latest/configuration.html](http://sqlalchemy-searchable.readthedocs.org/en/latest/configuration.html)

## License

<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>.

