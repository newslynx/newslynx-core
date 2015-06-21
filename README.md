# newslynx

**This is still a WIP and we should be officially open-sourcing the codebase in late June/July 2015. For now, please read [the report](http://towcenter.org/research/the-newslynx-impact-tracker-produced-these-key-ideas/) we published for the [TowCenter](http://towcenter.org) on our prototype.**
 

## (Re)Setting up the dev environment

* Install `newslynx`, prefrerably in a virtual environment.

```
git clone https://github.com/newslynx/newslynx.git
cd newslynx
python setup.py install
```

* (re)create a `postgresql` database

```
dropdb newslynx 
createdb newslynx
```

* fill out [`example_config/config.yaml`](example_config/config.yaml) and move it to `~/.newslynx/config.yaml` 
    
* modify default recipes and tags in [`example_config/defaults/recipes/`](example_config/defaults/recipes/) and [`example_config/defaults/tags/`](example_config/defaults/tags/), respectively. These tags and recipes will be created everytime a new organization is added.

* initialize the database:

```
newslynx init
```

* populate with sample data

```
newslynx gen_random_data
```

* start the server in debug mode

```
newslynx runserver -d
```

* start a production server via `gunicorn`

```
./run
```

* IGNORE THIS ERROR:

This is a result of our extensive use of `gevent`. We haven't yet figured out how to properly suppress this error. See more details [here](http://stackoverflow.com/questions/8774958/keyerror-in-module-threading-after-a-successful-py-test-run).

```
Exception KeyError: KeyError(4332017936,) in <module 'threading' from '/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/threading.pyc'> ignored
```



## TODO 

- [x] Migrate common utilites from other repos into single repo.
- [x] Create Database Schema / Models 
- [x] Create Blueprint-based app workflow 
- [x] Re-implement OAuth endpoints 
- [x] Implement Facebook OAuth
- [x] Re-implement User / Login API
- [x] Implement Org API
- [x] Re-implement Settings API
- [x] Re-implement Events API
    - [x] Implement Postgres-based search
    - [x] Make multiple search vectors
- [ ] Re-implement Things API (aka Articles)
    - [x] Implement Postgres-based search
    - [x] Make multiple search vectors
- [x] Re-implement Tags API
- [x] Write out SousChefs JSONSchema
- [x] Write out initial schemas:
    - [x] article
    - [x] twitter-list
    - [x] twitter-user
    - [x] facebook-page
- [x] Write out default recipes + tags:
    - [x] article
    - [x] twitter-list
    - [x] twitter-user
    - [x] facebook-page
    - [x] promotion impact tag
- [x] Update create org endpoint to generate default recipes + tags.
- [x] Implement SousChefs API 
- [x] Implement Recipes API
- [x] Implement Thing Creation API
- [ ] Implement SQL Query API
- [x] Implement Extraction API
- [x] Implement Event Creation API
- [x] Create thumbnails for images.
   - [x] Add thumbnail worker redis cache.
- [ ] Implement Metrics API:
    - [x] Create metrics table which contains information
          on each metric (name, timeseries agg method,
          summary agg method, cumulative, metric 
          category, level, etc)
    - [x] Faceted metrics only need to declare their name 
          name, not all their potential facet values.
    - [x] Sous Chefs that create metrics must declare
          which metrics they create.
    - [ ] When a recipe is created for a sous chef that 
          creates metrics, these metrics should be created for the associated organization.
    - [x] Timeseries Metrics for things will only be   
          collected 30 days after publication. After 
          this period an article moves into an "archived"
          state. 
    - [x] Each Organization should have the following 
          views/apis with these respective 
          functionalites:
          - [x Timeseries Aggregations
             - [x] Thing level 
                - [x] By hour + day + month
             - [ ] Subject Tag Level (subsequent aggregations of things)
                - [ ] By day.
             - [x] Impact Tag Level (aggregations of events => non customizable.)
             - [ ] Org Level (This should include 
                   summaries of thing-level statistics,
                   tag-level statistics, and event-level 
                   statistics)
                - [ ] By day, month
             - [x] optionally return cumulative sums when
                   appropriate
          - [ ] Summary Stats
            - [ ] Impact Tag Level
            - [ ] Subject Tag Level
            - [ ] Impact Tag Level
            - [ ] Organization Level
            - [ ] These should be Archived Every day. and percent changes should be computed over time periods.

- [ ] Implement Reports API (Are these just metrics?)
    - [ ] reports are json objects
    - [ ] reports can be rendered with Jinja templates
    - [ ] reports can be rendered as pdfs 
        * see: https://pypi.python.org/pypi/pdfkit or
         http://stackoverflow.com/questions/23359083/how-to-convert-webpage-into-pdf-by-using-python 
         or just force user s to "save as pdf"
    - [ ] reports can be saved + archived up to X days.
    - [ ] reports can o
- [ ] Implement Redis Task Queue For Recipe Running
    - [ ] Create gevent worker class to avoid reliance on
          os.fork
    - [ ] Figure out how to rate limit requests.
- [x] Implement Modular SousChefs Class
- [x] Figure out how best to use OAuth tokens in SousChefs. Ideally these should not be exposed to users.
- [x] Implement API client
- [ ] Re-implement SousChefs
    - [ ] RSS Feeds => Thing
    - [ ] Google Analytics => Metric
    - [ ] Google Alerts => Event
    - [ ] Social Shares => Metric
    - [ ] Homepage Promotions => Metric
    - [ ] Twitter Promotions => Metric
    - [ ] Facebook Promotions => Metric
    - [ ] Twitter List => Event 
    - [ ] Twitter User => Event 
    - [ ] Facebook Page => Event 
    - [ ] Reddit => Event
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

