-- This function allows truncation of dates by arbitrary buckets of minutes within an hour
CREATE OR REPLACE FUNCTION date_trunc_by_minutes(int, timestamp with time zone) 
RETURNS timestamp with time zone AS $$ 
BEGIN
  IF $1 > 30 THEN
     RAISE EXCEPTION 'the number of hours must be <= 30';
  END IF;
  RETURN 
    date_trunc('hour', $2) + 
    (((width_bucket(extract(minute FROM $2), 0, 60, 60/$1::int) - 1) * $1)::text || ' minutes')::interval;
END;
$$ LANGUAGE plpgsql;

-- This function allows truncation of dates by arbitrary buckets of hours within a day
CREATE OR REPLACE FUNCTION date_trunc_by_hours(int, timestamp with time zone) 
RETURNS timestamp with time zone AS $$ 
BEGIN
  IF $1 > 12 THEN
     RAISE EXCEPTION 'the number of hours must be <= 12';
  END IF;
  RETURN 
    date_trunc('day', $2) + 
    (((width_bucket(extract(hour FROM $2), 0, 24, 24/$1::int) - 1) * $1)::text || ' hours')::interval;
END;
$$ LANGUAGE plpgsql;


-- This function allows for the creation of a timeseries of
-- unique thing_ids and timestamps, grouped by arbitrary buckets
-- of minutes or hours. This function is useful when pivoting
-- metrics to create non-sparse timeseries
-- USAGE:
--     select * from thing_metrics_calendar('30 minutes')
CREATE OR REPLACE FUNCTION thing_metrics_calendar(text) 
RETURNS TABLE(datetime timestamp with time zone, thing_id int) AS
$BODY$
DECLARE
   t_id int;
   bucket int;
   unit text;
BEGIN
   -- parse argument
   bucket := split_part($1, ' ', 1)::int;
   unit := split_part($1, ' ', 2);
   IF unit NOT IN {'minutes', 'hours', 'hour', 'minute'} THEN
       RAISE EXCEPTION 'unit must be of minutes, minue, hours, or hour';
   END IF;
   FOR t_id IN 
       SELECT distinct(id) FROM things
       ORDER BY id asc
   LOOP
      RETURN QUERY EXECUTE 
        'WITH cal AS (
            WITH mm AS (
                SELECT 
                    MIN(date_trunc_by_' || unit || '(' || bucket || ', metrics.created)) AS minmin,
                    MAX(date_trunc_by_' || unit || '(' || bucket || ', metrics.created)) AS maxmax,
                    thing_id, org_id
                FROM metrics 
                    WHERE metrics.thing_id=' || t_id || '
                    AND metrics.created IS NOT NULL and metrics.level = ''thing'' 
                    GROUP BY metrics.thing_id, metrics.org_id)
            SELECT 
                generate_series(mm.minmin , mm.maxmax , '''|| $1 || '''::interval) AS datetime,
                thing_id
            FROM mm
            )
       SELECT org_id, thing_id, datetime FROM cal ORDER BY datetime ASC';
   END LOOP;
END
$BODY$
LANGUAGE plpgsql;

-- This function allows for the creation of a timeseries of
-- unique org_ids and timestamps, grouped by arbitrary buckets
-- of minutes or hours. This function is useful when pivoting
-- metrics to create non-sparse timeseries.
-- USAGE:
--     select * from thing_metrics_calendar('30 minutes')
CREATE OR REPLACE FUNCTION org_metrics_calendar(text) 
RETURNS TABLE(datetime timestamp with time zone, org_id int) AS
$BODY$
DECLARE
   org_id int;
   bucket int;
   unit text;
BEGIN
   -- parse argument
   bucket := split_part($1, ' ', 1)::int;
   unit := split_part($1, ' ', 2);
   IF unit NOT IN {'minutes', 'hours', 'hour', 'minute'} THEN
       RAISE EXCEPTION 'unit must be of minutes, minue, hours, or hour';
   END IF;
   FOR org_id IN 
       SELECT distinct(id) FROM organizations
       ORDER BY id asc
   LOOP
      RETURN QUERY EXECUTE 
        'WITH cal AS (
            WITH mm AS (
                SELECT 
                    MIN(date_trunc_by_' || unit || '(' || bucket || ', metrics.created)) AS minmin,
                    MAX(date_trunc_by_' || unit || '(' || bucket || ', metrics.created)) AS maxmax,
                    org_id
                FROM metrics 
                    WHERE metrics.org_id=' || org_id || '
                    AND metrics.created IS NOT NULL and metrics.level = ''org'' 
                    GROUP BY metrics.org_id)
            SELECT 
                generate_series(mm.minmin , mm.maxmax , '''|| $1 || '''::interval) AS datetime,
                org_id
            FROM mm
            )
       SELECT org_id, datetime FROM cal ORDER BY datetime ASC';
   END LOOP;
END
$BODY$
LANGUAGE plpgsql;
