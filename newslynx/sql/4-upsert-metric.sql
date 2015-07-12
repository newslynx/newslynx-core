-- upsert content metrics timeseries
CREATE OR REPLACE FUNCTION "upsert_content_metric_timeseries"(
    "_org_id" INT,
    "_content_item_id" INT,
    "_datetime" timestamp with time zone,
    "_metrics" TEXT
) 
RETURNS VOID AS
$$
BEGIN
    LOOP
        -- first try to update the row
        UPDATE content_metric_timeseries 
        SET metrics = json_merge(metrics, "_metrics"::json),
            updated = current_timestamp
        WHERE
            org_id = "_org_id" AND
            datetime = "_datetime" AND
            content_item_id = "_content_item_id";
            
        IF found THEN
            RETURN;
        END IF;
        -- not there, so try to insert the key
        -- if someone else inserts the same key concurrently,
        -- we could get a unique-key failure
        BEGIN
            INSERT INTO content_metric_timeseries
            VALUES ("_org_id", "_content_item_id", "_datetime", "_metrics"::json, current_timestamp);
            RETURN;
        EXCEPTION WHEN unique_violation THEN
            -- do nothing, and loop to try the UPDATE again
        END;
    END LOOP;
END;
$$
LANGUAGE plpgsql;

-- upsert content metrics summary
CREATE OR REPLACE FUNCTION "upsert_content_metric_summary"(
    "_org_id" INT,
    "_content_item_id" INT,
    "_metrics" TEXT
) 
RETURNS VOID AS
$$
BEGIN
    LOOP
        -- first try to update the row
        UPDATE content_metric_summary 
        SET metrics = json_merge(metrics, "_metrics"::json)
        WHERE
            org_id = "_org_id" AND
            content_item_id = "_content_item_id";
            
        IF found THEN
            RETURN;
        END IF;
        -- not there, so try to insert the key
        -- if someone else inserts the same key concurrently,
        -- we could get a unique-key failure
        BEGIN
            INSERT INTO content_metric_summary
            VALUES ("_org_id", "_content_item_id", "_metrics"::json);
            RETURN;
        EXCEPTION WHEN unique_violation THEN
            -- do nothing, and loop to try the UPDATE again
        END;
    END LOOP;
END;
$$
LANGUAGE plpgsql;

-- upsert org metrics timeseries
CREATE OR REPLACE FUNCTION "upsert_org_metric_timeseries"(
    "_org_id" INT,
    "_datetime" timestamp with time zone,
    "_metrics" TEXT
) 
RETURNS VOID AS
$$
BEGIN
    LOOP
        -- first try to update the row
        UPDATE org_metric_timeseries 
        SET metrics = json_merge(metrics, "_metrics"::json),
            updated = current_timestamp
        WHERE
            org_id = "_org_id" AND
            datetime = "_datetime";
            
        IF found THEN
            RETURN;
        END IF;
        -- not there, so try to insert the key
        -- if someone else inserts the same key concurrently,
        -- we could get a unique-key failure
        BEGIN
            INSERT INTO org_metric_timeseries
            VALUES ("_org_id", "_datetime", "_metrics"::json, current_timestamp);
            RETURN;
        EXCEPTION WHEN unique_violation THEN
            -- do nothing, and loop to try the UPDATE again
        END;
    END LOOP;
END;
$$
LANGUAGE plpgsql;


-- upsert org metric summary
CREATE OR REPLACE FUNCTION "upsert_org_metric_summary"(
    "_org_id" INT,
    "_metrics" TEXT
) 
RETURNS VOID AS
$$
BEGIN
    LOOP
        -- first try to update the row
        UPDATE org_metric_summary 
        SET metrics = json_merge(metrics, "_metrics"::json)
        WHERE org_id = "_org_id";

        IF found THEN
            RETURN;
        END IF;
        -- not there, so try to insert the key
        -- if someone else inserts the same key concurrently,
        -- we could get a unique-key failure
        BEGIN
            INSERT INTO org_metric_summary
            VALUES ("_org_id", "_metrics"::json);
            RETURN;
        EXCEPTION WHEN unique_violation THEN
            -- do nothing, and loop to try the UPDATE again
        END;
    END LOOP;
END;
$$
LANGUAGE plpgsql;