name: Content Metric Summary
slug: content-metric-summary
description: |
    Rollup content metrics timseries + event tag metrics for 
    all of an organization's content items.
runs: newslynx.sc.internal.content_metrics.Summarize
creates: metrics
option_order: []
options:
    
    hours_since_last_update:
        input_type: number
        value_types:
            - numeric
        required: false
        default: 5
        help:
            placeholder: propalpatine

    interval:
        input_type: number 
        value_types:
            - numeric
        required: false
        default: 3600


metrics:

    total_events:
        display_name: Total Events
        aggregation: sum
        level: all
        cumulative: false
        faceted: false
        timeseries: false

    total_event_tags:
        display_name: Total Event Tags
        aggregation: sum
        level: all
        cumulative: false
        faceted: false
        timeseries: false

    institution_level_events:
        display_name: Institution Level Events
        aggregation: sum
        level: all
        cumulative: false
        faceted: false
        timeseries: false

    media_level_events:
        display_name: Media Level Events
        aggregation: sum
        level: all
        cumulative: false
        faceted: false
        timeseries: false

    community_level_events:
        display_name: Community Level Events
        aggregation: sum
        level: all
        cumulative: false
        faceted: false
        timeseries: false

    individual_level_events:
        display_name: Individual Level Events
        aggregation: sum
        level: all
        cumulative: false
        faceted: false
        timeseries: false

    internal_level_events:
        display_name: Internal Level Events
        aggregation: sum
        level: all
        cumulative: false
        faceted: false
        timeseries: false

    promotion_category_events:
        display_name: Promotion Category Events
        aggregation: sum
        level: all
        cumulative: false
        faceted: false
        timeseries: false

    citation_category_events:
        display_name: Citation Category Events
        aggregation: sum
        level: all
        cumulative: false
        faceted: false
        timeseries: false

    change_category_events:
        display_name: Change Category Events
        aggregation: sum
        level: all
        cumulative: false
        faceted: false
        timeseries: false

    achievement_category_events:
        display_name: Achievement Category Events
        aggregation: sum
        level: all
        cumulative: false
        faceted: false
        timeseries: false

    other_category_events:
        display_name: Other Category Events
        aggregation: sum
        level: all
        cumulative: false
        faceted: false
        timeseries: false
    