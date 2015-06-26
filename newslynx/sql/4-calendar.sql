-- A function for creating a lookup table to make timeseries non-sparse.
CREATE OR REPLACE FUNCTION content_metric_calendar(
  text, 
  "c_ids" anyarray, 
  "after" timestamp with time zone DEFAULT '2000-01-01',
  "before" timestamp with time zone DEFAULT '2100-01-01') 
RETURNS TABLE(content_item_id int, datetime timestamp with time zone) AS
$BODY$
DECLARE
   c_id int;
   bucket int;
   unit text;
BEGIN
  -- parse argument
  unit := split_part($1, ' ', 2);
  IF unit = 'days' THEN
    unit := 'day';
  END IF;
  IF unit = 'hours' THEN
    unit := 'hour';
  END IF;

  FOR c_id IN
    SELECT unnest("c_ids")
  LOOP
    -- generate calendar
    RETURN QUERY EXECUTE 
      'WITH cal AS (
          WITH mm AS (
              SELECT 
                  MIN(date_trunc('''|| unit || ''', datetime)) AS minmin,
                  MAX(date_trunc('''|| unit || ''', datetime)) AS maxmax,
                  content_item_id
              FROM content_metric_timeseries
                  WHERE content_item_id=' || c_id || ' AND 
                        datetime >='''|| "after" || ''' AND 
                        datetime <='''|| "before" || '''
                  GROUP BY content_item_id)
          SELECT
              content_item_id,
              generate_series(mm.minmin , mm.maxmax , '''|| $1 || '''::interval) AS datetime
          FROM mm
          )
     SELECT content_item_id, datetime FROM cal ORDER BY datetime ASC';
  END LOOP;
END
$BODY$
LANGUAGE plpgsql;

-- A function for creating a lookup table to make timeseries non-sparse.
CREATE OR REPLACE FUNCTION org_metric_calendar(
  text, 
  "o_ids" anyarray, 
  "after" timestamp with time zone DEFAULT '2000-01-01',
  "before" timestamp with time zone DEFAULT '2100-01-01') 
RETURNS TABLE(org_id int, datetime timestamp with time zone) AS
$BODY$
DECLARE
   o_id int;
   bucket int;
   unit text;
BEGIN
  -- parse argument
  unit := split_part($1, ' ', 2);
  IF unit = 'days' THEN
    unit := 'day';
  END IF;
  IF unit = 'hours' THEN
    unit := 'hour';
  END IF;
  FOR o_id IN
    SELECT unnest("o_ids")
  LOOP
    -- generate calendar
    RETURN QUERY EXECUTE 
      'WITH cal AS (
          WITH mm AS (
              SELECT 
                  MIN(date_trunc('''|| unit || ''', datetime)) AS minmin,
                  MAX(date_trunc('''|| unit || ''', datetime)) AS maxmax,
                  org_id
              FROM org_metric_timeseries
                  WHERE org_id=' || o_id || ' AND 
                        datetime >='''|| "after" || ''' AND 
                        datetime <='''|| "before" || '''
                  GROUP BY org_id
          )
          SELECT
              org_id,
              generate_series(mm.minmin , mm.maxmax , '''|| $1 || '''::interval) AS datetime
          FROM mm
          )
     SELECT org_id, datetime FROM cal ORDER BY datetime ASC';
  END LOOP;
END
$BODY$
LANGUAGE plpgsql;