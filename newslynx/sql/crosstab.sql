WITH stats as (
    SELECT 
        thing_id, datetime, 
        SUM(coalesce(on_homepage, 0)) AS on_homepage, 
        SUM(coalesce(pageviews, 0)) AS pageviews, 
        SUM(coalesce(twitter_shares, 0)) AS twitter_shares 

    from crosstab(
        'SELECT 
            thing_id, date_trunc(''hour'', created) AS datetime, name, SUM(value) AS value 
         FROM metrics 
         WHERE created IS NOT NULL AND level = ''thing''
         GROUP BY datetime, name, thing_id
         ORDER BY datetime, name ASC', 
        'SELECT 
            distinct(name) 
         FROM metrics 
         WHERE created IS NOT NULL 
         AND level = ''thing'' 
         ORDER BY name ASC'
    ) as 
        ct(
            thing_id int, 
            datetime timestamp with time zone, 
            on_homepage numeric, 
            pageviews numeric, 
            twitter_shares numeric
        )
    GROUP BY thing_id, datetime 
    ORDER BY datetime, thing_id ASC
),

calendar AS (
    select datetime, thing_id, org_id from thing_metrics_calendar('1 hour')
)

SELECT calendar.org_id, 
       calendar.thing_id, 
       calendar.datetime,
       coalesce(on_homepage, 0) as on_homepage, 
       coalesce(pageviews, 0) as pageviews, 
       coalesce(twitter_shares, 0) as twitter_shares 
FROM calendar
LEFT JOIN stats ON calendar.datetime = stats.datetime AND calendar.thing_id = stats.thing_id
ORDER BY calendar.datetime, calendar.thing_id ASC
