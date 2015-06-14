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



