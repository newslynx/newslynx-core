CREATE OR REPLACE FUNCTION content_idx(anyarray, anyelement)
  RETURNS INT AS 
$$
  SELECT i FROM (
     SELECT generate_series(array_lower($1,1),array_upper($1,1))
  ) g(i), content
  WHERE $1[i] = $2
  LIMIT 1;
$$ LANGUAGE SQL IMMUTABLE;

CREATE OR REPLACE FUNCTION events_idx(anyarray, anyelement)
  RETURNS INT AS 
$$
  SELECT i FROM (
     SELECT generate_series(array_lower($1,1),array_upper($1,1))
  ) g(i), events
  WHERE $1[i] = $2
  LIMIT 1;
$$ LANGUAGE SQL IMMUTABLE;