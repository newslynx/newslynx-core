# newslynx

the API and SousChefs that Power Newslynx.


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

You can ignore the following error if you see it

````
Exception KeyError: KeyError(4384375024,) in <module 'threading' from '/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/threading.pyc'> ignored
````

* populate with sample data

```
newslynx gen_random_data
```

* start the server in debug mode

```
newslynx runserver -d
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
- [x] Re-implement Things API (aka Articles)
    - [x] Implement Postgres-based search
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
- [ ] Implement Thing Creation API
- [ ] Implement Event Creation API
- [ ] Implement Metrics API:
    - [x] Figure out how to use `tablefunc` for pivot tables.
    - [ ] Create metrics table which contains information
          on each metric (name, timeseries agg method,
          summary agg method, cumulative, metric 
          category, level, etc)
    - [ ] Faceted metrics only need to declare the facet 
          name, not all their potential facet values.
    - [ ] Sous Chefs that create metrics must declare
          which metrics they create.
    - [ ] When a recipe is created for a sous chef that 
          creates metrics, these metrics should be created for the associated organization
    - [ ] When an org adds/modifies a calculated metric 
          these metrics must be immediately created and 
          all of their views / reports must be immediately refreshed. This will obviously 
          happen in a background task.
    - [ ] Upon subsequent view refreshes, calculated
          metrics must be included.
    - [ ] Timeseries Metrics for things will only be   
          collected 30 days after publication. After 
          this period an article moves into an "archived"
          state. 
    - [ ] Each Organization should have the following 
          views/apis with these respective 
          functionalites:
          - [ ] Timeseries Aggregations
             - [ ] Thing level 
                - [ ] By hour + day
             - [ ] Tag Level (subsequent aggregations of things)
                - [ ] By hour + day, month
             - [ ] Org Level (This should include 
                   summaries of thing-level statistics,
                   tag-level statistics, and event-level 
                   statistics)
                - [ ] By hour + day, month
             - [ ] optionally return cumulative sums when
                   appropriate
          - [ ] Summary Stats
            - [ ] Thing Level
            - [ ] Tag Level
            - [ ] Organization Level

- [ ] Implement Reports API (Are these just metrics?)
    - [ ] reports are json objects
    - [ ] reports can be rendered with html templates
    - [ ] reports can be rendered as pdfs 
        * see: https://pypi.python.org/pypi/pdfkit or
         http://stackoverflow.com/questions/23359083/how-to-convert-webpage-into-pdf-by-using-python 
         or just force user s to "save as pdf"
    - [ ] reports can be saved + archived up to X days.
    - [ ] reports can o
- [ ] Implement Redis Task Queue For Recipe Running
    - [ ] Create gevent worker class to avoid reliance on
          os.fork
- [ ] Implement Modular SousChefs
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
- [x] Implement Recipe scheduler
- [ ] Implement Admin Panel
- [ ] Migrate Core Beta Users (Lauren, Lindsay, Blair)
- [ ] Automate Deployment
- [ ] App Integration
- [ ] Document, Document, Document

## References

### API Design

* [http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api](http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api)

### Crosstab in Postgres
* [http://www.postgresonline.com/journal/archives/14-CrossTab-Queries-in-PostgreSQL-using-tablefunc-contrib.html](http://www.postgresonline.com/journal/archives/14-CrossTab-Queries-in-PostgreSQL-using-tablefunc-contrib.html)

### filling in zeros for a timezeries
* [http://stackoverflow.com/questions/346132/postgres-how-to-return-rows-with-0-count-for-missing-data]

### fetching column names from table
* [http://www.postgresql.org/message-id/AANLkTilsjTAXyN5DghR3M2U4c8w48UVxhov4-8igMpd1@mail.gmail.com](http://www.postgresql.org/message-id/AANLkTilsjTAXyN5DghR3M2U4c8w48UVxhov4-8igMpd1@mail.gmail.com)

### timeseries tips
* [http://no0p.github.io/postgresql/2014/05/08/timeseries-tips-pg.html](http://no0p.github.io/postgresql/2014/05/08/timeseries-tips-pg.html)

### Getting bigger with flask (+ dynamic subdomains):
* [http://maximebf.com/blog/2012/11/getting-bigger-with-flask/#.VVYvUZNVhBc](http://maximebf.com/blog/2012/11/getting-bigger-with-flask/#.VVYvUZNVhBc)

### Nonblocking with flask, gevent, + psycopg2
* [https://github.com/kljensen/async-flask-sqlalchemy-example](https://github.com/kljensen/async-flask-sqlalchemy-example)
