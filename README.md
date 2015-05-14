# newslynx

the API and SousChefs that Power Newslynx.


## (Re)Setting up the dev environment

* Clone this repository and install `newslynx`
    
    - preferably do this in a virtual environment.

```
git clone https://github.com/newslynx/newslynx
pip install -e newslynx
```

* (re)create a `postgresql` database

```
psql >
username=# drop database newslynx;
username=# create database newslynx;
```

* fill out [`sample_config.yaml`](sample_config.yaml) and put it somewhere safe. 
    
    - MORE DETAILS TK HERE

* set the environment variable `NEWSLYNX_CONFIG_FILE` to point to the absolute path of your config file.

* initialize the database:

```
newslynx init
```

* populate with sample data

```
python scripts/gen_random_data.py
```

* start the server in debug mode

```
newslynx runserver -r -d
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
- [ ] Re-implement Things API (aka Articles)
    - [x] Implement Postgres-based search
- [x] Re-implement Tags API
- [x] Write out SousChefs JSONSchema
- [x] Write out initial schemas:
    - [x] article
    - [x] twitter-list
    - [x] twitter-user
    - [x] facebook-page
- [ ] Write out default recipes + tags:
    - [ ] article
    - [ ] twitter-list
    - [ ] twitter-user
    - [ ] facebook-page
    - [ ] promotion impact tag
- [ ] Update create org endpoint to generate default recipes + tags.
- [ ] Implement SousChefs API 
- [ ] Implement Recipes API 
- [ ] Implement Thing Creation API
- [ ] Implement Event Creation API
- [ ] Implement Metrics API:
    - [x] Figure out how to use `tablefunc` for pivot tables.
- [ ] Implement Reports API (Are these just metrics?)
    - [ ] Figure out how to use `pypostgresql` for custom postgres functions.
- [ ] Implement Task Queue (Celery, Redis?)
- [ ] Implement Modular SousChefs
- [ ] Figure out how best to use OAuth tokens in SousChefs. Ideally these should not be exposed to users.
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
- [ ] Implement Recipe scheduler
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
