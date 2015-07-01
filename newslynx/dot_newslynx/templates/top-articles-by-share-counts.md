## Top **{{data.range.number}}** Content Items by Share Counts
For the week of **{{data.range.start}}** to **{{data.range.end}}**

This report with ID: *{{id}}* was created at `{{created}}`.

{% for content_item in data.content_items %}

### {{content_item.title}}
Twitter Shares: **{{content_item.metrics.twitter_shares}}**

{% endfor %}
