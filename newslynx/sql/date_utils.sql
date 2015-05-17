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
