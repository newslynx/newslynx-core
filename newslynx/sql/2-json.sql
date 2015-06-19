-- remove keys from a json object
CREATE OR REPLACE FUNCTION "json_del_keys"("json" json, VARIADIC "keys_to_delete" TEXT[])
  RETURNS json
  LANGUAGE sql
  IMMUTABLE
  STRICT
AS $function$
SELECT COALESCE(
  (SELECT ('{' || string_agg(to_json("key") || ':' || "value", ',') || '}')
   FROM json_each("json")
   WHERE "key" <> ALL ("keys_to_delete")),
  '{}'
)::json
$function$;

--- merge json objects
CREATE OR REPLACE FUNCTION json_merge(left JSON, right JSON)
RETURNS JSON AS $$
  import json
  l, r = json.loads(left), json.loads(right)
  if not l:
      return json.dumps(r)
  if not r:
      return json.dumps(l)
  l.update(r)
  return json.dumps(l)
$$ LANGUAGE PLPYTHONU;

--- delete an individual key
CREATE OR REPLACE FUNCTION "json_del_key"(
  "json"          json,
  "key_to_del"    TEXT
)
  RETURNS json
  LANGUAGE sql
  IMMUTABLE
  STRICT
AS $function$
SELECT CASE
  WHEN ("json" -> "key_to_del") IS NULL THEN "json"
  ELSE (SELECT concat('{', string_agg(to_json("key") || ':' || "value", ','), '}')
          FROM (SELECT *
                  FROM json_each("json")
                 WHERE "key" <> "key_to_del"
               ) AS "fields")::json
END
$function$;


--- set an individual key
CREATE OR REPLACE FUNCTION "json_set_key"(
  "json"          json,
  "key_to_set"    TEXT,
  "value_to_set"  anyelement
)
  RETURNS json
  LANGUAGE sql
  IMMUTABLE
  STRICT
AS $function$
SELECT concat('{', string_agg(to_json("key") || ':' || "value", ','), '}')::json
  FROM (SELECT *
          FROM json_each("json")
         WHERE "key" <> "key_to_set"
         UNION ALL
        SELECT "key_to_set", to_json("value_to_set")) AS "fields"
$function$;


--- delete a path
CREATE OR REPLACE FUNCTION "json_del_path"(
  "json"          json,
  "key_path"      TEXT[]
)
  RETURNS json
  LANGUAGE sql
  IMMUTABLE
  STRICT
AS $function$
SELECT CASE
  WHEN ("json" -> "key_path"[l] ) IS NULL THEN "json"
  ELSE
     CASE COALESCE(array_length("key_path", 1), 0)
         WHEN 0 THEN "json"
         WHEN 1 THEN "json_del_key"("json", "key_path"[l])
         ELSE "json_set_key"(
           "json",
           "key_path"[l],
           "json_del_path"(
             COALESCE(NULLIF(("json" -> "key_path"[l])::text, 'null'), '{}')::json,
             "key_path"[l+1:u]
           )
         )
       END
    END
  FROM array_lower("key_path", 1) l,
       array_upper("key_path", 1) u
$function$;



