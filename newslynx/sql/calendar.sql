-- This function allows for the creation of a timeseries of
-- unique thing_ids and timestamps, grouped by arbitrary buckets
-- of minutes or hours. This function is useful when pivoting
-- metrics to create non-sparse timeseries
-- USAGE:
--     select * from thing_metrics_calendar('30 minutes')
CREATE OR REPLACE FUNCTION thing_metrics_calendar(text) 
RETURNS TABLE(org_id int, thing_id int, datetime timestamp with time zone) AS
$BODY$
DECLARE
   t_id int;
   bucket int;
   unit text;
BEGIN
   -- parse argument
   bucket := split_part($1, ' ', 1)::int;
   unit := split_part($1, ' ', 2);
   IF unit IN ('minute', 'hour') THEN
      unit := unit || 's';
   END IF;
   IF unit NOT IN ('minutes', 'hours') THEN
       RAISE EXCEPTION 'unit must be of minutes or hours';
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
                org_id, thing_id,
                generate_series(mm.minmin , mm.maxmax , '''|| $1 || '''::interval) AS datetime
            FROM mm
            )
       SELECT org_id, thing_id, datetime FROM cal ORDER BY datetime, org_id, thing_id ASC';
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
   IF unit IN ('minute', 'hour') THEN
      unit := unit || 's';
   END IF;
   IF unit NOT IN ('minutes', 'hours') THEN
       RAISE EXCEPTION 'unit must be of minutes or hours';
   END IF;
   FOR org_id IN 
       SELECT distinct(id) FROM orgs
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
       SELECT datetime, org_id FROM cal ORDER BY datetime ASC';
   END LOOP;
END
$BODY$
LANGUAGE plpgsql;