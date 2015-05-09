# newslynx

the API and Data Collection Tasks that Power Newslynx.

## Questions

- [ ] What are traffic-by-domain metrics? These will be impossible to put in a pivot table.
- [ ] What are trackbacks?  Should we make a special "Link" class?
- [ ]

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
- [ ] Implement Metrics API:
    -
    - [ ] Figure out how to use `tablefunc` for pivot tables.
- [ ] Implement Reports API (Are these just metrics?)
    - [ ] Figure out how to use `pypostgresql` for custom postgres functions.
- [ ] Implement Tasks API 
- [ ] Implement Recipes API 
- [ ] Implement Task Queue (Celery, Redis?)
- [ ] Implement Thing Creation API
- [ ] Implement Event Creation API
- [ ] Implement Modular Tasks
- [ ] Figure out how best to use OAuth tokens in Tasks. Ideally these should not be exposed to users.
- [x] Implement API client
- [ ] Re-implement Tasks
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
    - [ ] 
- [ ] Implement New Tasks 
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
