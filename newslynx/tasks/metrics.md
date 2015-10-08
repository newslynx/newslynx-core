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
 S[1]                                          [content comparison]
   \                                  S[2]      /
    \------[org summary] <-> C[9]       \      / 
        	 /       \                   \    /
        	/         \----- R[5] ----[content summary] <-> C[10]
           /                               \
         R[7]                              R[6]
           \                                  \
C[11] <-> [org timeseries]--- R[8] ---[content timeseries] <-> C[12]
              |                                 |
             S[3]                              S[4]


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
		type: # anything but computed
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
		type: # anything but computed
		...

S[3]: [org timeseries] metrics imported by Sous Chefs.

Example config:

metrics:
	my_org_timeseries_metric:
		org_levels:
			- timeseries
			- summary # optionally rollup by org id.
		content_levels: []
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
		...

R[5]: Metrics which can be rolledup from the [content summary] to [org summary] level.

Example config:

metrics:
	my_metric:
		org_levels:
			- summary # cannot include timeseries.
		content_levels:
			- summary
		agg: min/max/avg/median/sum # will default to type's default

R[6]: Metrics which can be rolledup from the [content timeseries] to [content summary] level.

Example config:

metrics:
	my_metric:
		org_levels: []  # can also include timeseries and summary
		content_levels:
			- summary
			- timeseries
		agg: min/max/avg/median/sum # will default to type's default

R[7]: Metrics which can be rolledup from the [org timeseries] to [org summary] level.

Example config:

metrics:
	my_metric:
		org_levels:
			- summary 
			- timeseries
		content_levels: [] # cannot include any content levels
		agg: min/max/avg/median/sum # will default to type's default

R[8]: Metrics which can be rolledup from the [content timeseries] to [org timeseries] level.

Example config:

metrics:
	my_metric:
		org_levels:
			- timeseries # can also include summary
		content_levels:
			- timeseries # can also include summary
		agg: min/max/avg/median/sum # will default to type's default


C[9]: Metrics which are computed on top of [org summary] metrics.

NOTE: You cannot create computed metrics which reference other computed metrics. You must include the original metric's formula in the formula of subsequent computed metrics instead. You might also consider creating a Sous Chef which computes these metrics at regular intervals and sends them back to the API, thereby turning them into normal, non-computed metrics. 

In addition, metrics which are computed at lower levels can only be included at higher levels if the underlying metrics they're computed on are summarized to these higher levels, as well. Take care in ensuring that this is the case before creating a computed metric since failure to do will lead to unexpected, undocumented errors. 

Example config:

metrics:
	my_computed_metric:
		org_levels:
			- summary # cannot include timeseries
		content_levels: [] # cannot include content levels 
		type: computed
		formula: "{my_metric_1} - {my_metric_2}" # postgres syntax.

C[10]: Metrics which are computed on top of [content summary] metrics.

Example config:

metrics:
	my_computed_metric:
		org_levels:
			- summary # optionally rollup by org id
		content_levels:
			- summary # cannot include timeseries
		type: computed
		formula: "{my_metric_1} * {my_metric_2}" # postgres syntax.

C[10]: Metrics which are computed on top of [org timeseries] metrics.

Example config:

metrics:
	my_computed_metric:
		org_levels:
			- summary # optionally rollup by org id
		content_levels:
			- summary # cannot include timeseries
		type: computed
		formula: "{my_metric_1} * {my_metric_2}" # postgres syntax.                

```





