summarization is separate from computation!

content_levels:
	- timeseries 
	- summary 
	- comparison
org_levels:
	- timeseries
	- summary 
	- comparison 
type:
	- computed 
	- faceted 

Events:

1. summarize event + tag information into content summary
- [X]

Summarizations:

1. content timeseries => content summary [X]

- Summarizes the content timeseries data by content item id and inserts into the content summary table
- Includes computed metrics from the _timeseries_ level.
- config:
```
content_levels:
	- timeseries
	- summary
```
2. content timeseries => org timeseries

- Summarizes the timeseries data by hour and inserts into the org timeseries table.
- Includes computed metrics from the _timeseries_ level.
- config:
```
content_levels:
	- timeseries
org_levels:
	- timeseries
```

3. content summary => org summary
- Summarizes the summary data for an entire organization and inserts into the org summary table.
- Inlcudes computed metrics from the _content summary_ level
- config:
```
content_levels:
	- summary
org_levels:
	- summary
```

4. org timeseries => org summary 
- Summaries the org timeseries data and stores in the org summary table.
- Includes computed metrics from the _org timeseries_ level.
- config:
```
org_levels:
	- timeseries
	- summary
```

Computations:

**NOTE** 
1. content timeseries
content timeseries computations are done on-the-fly at the timeseries-level so as to ensure validity. they are, however, rolledup and treated as static metrics at the summary levels.

config:
```
type: computed
content_levels:
	- timeseries
org_levels:
	- timeseries
```

2. content summary
after metrics are rolledup from events + content timeseries, compute content_summary metrics.

3. org timeseries
after metrics are rolledup from content timeseries, compute org timeseries-level metrics

config:
```
type: computed
content_levels: []
org_levels:
	- timeseries
```
can run computations on summaries of content timeseries metrics and computed timeseries metrics which also exist at the org_timeseries level.

3. org summary
after metrics are rolledup from org timeseries + content summary, compute org summary-level metrics

Diagram

```
 S[1] 
   \          
    \------[org summary] <-> C[9]      S[2]    [content comparison]
        	 /       \                   \    /
        	/         \----- R[5] ----[content summary] <-> C[10]
           /                               \
         R[7]                              R[6]
           \                                  \
C[11] <-> [org timeseries]--- R[8] ---[content timeseries] <-> C[12]
              |                                 |
             S[3]                              S[4]

)

legend
------
S = Sous Chefs which import data to various
    metric levels.
R = Rollups which summarize data at one level to a higher level
C = Computed metrics which execute computations on metrics of one level 
    and store them as metrics of another level.

key
------
S[1]: [org summary] metrics imported by Sous Chefs.

Example config:
metrics:
	my_org_summary_metric:
		org_levels:
			- summary
		content_levels: []
		type: *anything but computed
		...

S[2]: [content summary] metrics imported by Sous Chefs.

Example config:
metrics:
	my_org_summary_metric:
		org_levels:
			- summary # optionally rollup by org id.
		content_levels:
			- summary

		content_levels: []
		type: *anything but computed
		...

S[3]: [org timeseries] metrics imported by Sous Chefs.

Example config:
metrics:
	my_org_timeseries_metric:
		org_levels:
			- timeseries
			- summary # optionally rollup by org id.
		content_levels: []
		type: *anything but computed
		...

S[4]: [content timeseries] imported by Sous Chefs.

Example config:
metrics:
	my_content_timeseries_metric:
		content_levels:
			- timeseries
			- summary # optionally rollup by content id.
		org_levels:
			- timeseries # optionally rollup by hour
			- summary # optionally rollup by org id.
		type: *anything but computed
		...

R[5]: Metrics which can be rolledup from the [content summary] to [org summary] level.

Example config:
metrics:
	my_org_timeseries_metric:
		org_levels:
			- summary
		content_levels:
			- summary
		...

R[6]: Metrics which can be rolledup from the [content summary] to [org summary] level.
Example config:
metrics:
	my_org_timeseries_metric:
		org_levels:
			- summary
		content_levels:
			- summary
		...



```





