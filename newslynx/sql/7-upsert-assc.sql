-- upsert org metric summary
CREATE OR REPLACE FUNCTION "upsert_events_tags"(
    "_event_id" INT,
    "_tag_id" INT
) 
RETURNS VOID AS
$$
    BEGIN
        INSERT INTO events_tags
        VALUES ("_event_id", "_tag_id");
        RETURN;
    EXCEPTION WHEN unique_violation THEN
        RETURN;
        -- do nothing, and loop to try the UPDATE again
    END;
$$
LANGUAGE plpgsql;

-- upsert org metric summary
CREATE OR REPLACE FUNCTION "upsert_content_items_events"(
    "_event_id" INT,
    "_content_item_id" INT
) 
RETURNS VOID AS
$$
    BEGIN
        INSERT INTO content_items_events
        VALUES ("_event_id", "_content_item_id");
        RETURN;
    EXCEPTION WHEN unique_violation THEN
        RETURN;
        -- do nothing, and loop to try the UPDATE again
    END;
$$
LANGUAGE plpgsql;

-- upsert org metric summary
CREATE OR REPLACE FUNCTION "upsert_content_items_tags"(
    "_content_item_id" INT,
    "_tag_id" INT
) 
RETURNS VOID AS
$$
    BEGIN
        INSERT INTO content_items_tags
        VALUES ("_tag_id", "_content_item_id");
        RETURN;
    EXCEPTION WHEN unique_violation THEN
        RETURN;
        -- do nothing, and loop to try the UPDATE again
    END;
$$
LANGUAGE plpgsql;

-- upsert org metric summary
CREATE OR REPLACE FUNCTION "upsert_content_items_authors"(
    "_content_item_id" INT,
    "_author_id" INT
) 
RETURNS VOID AS
$$
    BEGIN
        INSERT INTO content_items_authors
        VALUES ("_author_id", "_content_item_id");
        RETURN;
    EXCEPTION WHEN unique_violation THEN
        RETURN;
        -- do nothing, and loop to try the UPDATE again
    END;
$$
LANGUAGE plpgsql;