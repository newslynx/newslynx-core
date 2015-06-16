-- Compute a histogram.
CREATE OR REPLACE FUNCTION hist_sfunc (state INTEGER[], val REAL, min REAL, max REAL, nbuckets INTEGER) RETURNS INTEGER[] AS $$
DECLARE
  bucket INTEGER;
  i INTEGER;
BEGIN
  bucket := width_bucket(val, min, max, nbuckets - 1) - 1;
 
  IF state[0] IS NULL THEN
    FOR i IN SELECT * FROM generate_series(0, nbuckets - 1) LOOP
      state[i] := 0;
    END LOOP;
  END IF;
 
  state[bucket] = state[bucket] + 1;
 
  RETURN state;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
 
DROP AGGREGATE IF EXISTS histogram (REAL, REAL, REAL, INTEGER);
CREATE AGGREGATE histogram (REAL, REAL, REAL, INTEGER) (
       SFUNC = hist_sfunc,
       STYPE = INTEGER[]
);

-- Compute a median.
CREATE OR REPLACE FUNCTION _final_median(numeric[])
   RETURNS numeric AS
$$
   SELECT AVG(val)
   FROM (
     SELECT val
     FROM unnest($1) val
     ORDER BY 1
     LIMIT  2 - MOD(array_upper($1, 1), 2)
     OFFSET CEIL(array_upper($1, 1) / 2.0) - 1
   ) sub;
$$
LANGUAGE 'sql' IMMUTABLE;
 
DROP AGGREGATE IF EXISTS median(numeric);
CREATE AGGREGATE median(numeric) (
  SFUNC=array_append,
  STYPE=numeric[],
  FINALFUNC=_final_median,
  INITCOND='{}'
);