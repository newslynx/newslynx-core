"""
Generate Markdown documentation from a SousChef configurations.
"""
from traceback import format_exc
from jinja2 import Template

from newslynx.lib import doc
from newslynx.exc import SousChefDocError
from newslynx.models import sous_chef_schema

# template for Sous Chef documentation.
SC_OPTS_TMPL = Template("""
### {{ name }}


* {{ description }}
* This Sous Chef runs the python module `{{ runs }}`.
* API Slug: `{{ slug }}`


#### Usage

##### Standalone

Run this Sous Chef via the api, passing in arbitrary runtime options, and stream it's output.

```shell
$ newslynx api sous-chefs cook -d={{ filepath }} --passthrough **options
```

Run this Sous Chef via the api, and if applicable, send it's output to bulkload.

```shell
$ newslynx api sous-chefs cook -d={{ filepath }} **options
```

Do either of the above two, but pass in a recipe file

```shell
$ newslynx api sous-chefs cook -d=recipe.yaml
```

##### Recipes

Add this Sous Chef to your authenticated org

```shell
$ newslynx api sous-chefs create -d={{ filepath }}
```

Create a Recipe with this Sous Chef with command line options.

```shell
$ newslynx api recipes create sous_chef={{ slug }} **options
```

Alternatively pass in a recipe file.

```shell
$ newslynx api recipes create sous_chef={{ slug }} --data=recipe.yaml
```

Save the outputted `id` of this recipe, and execute it via the API.

**NOTE** This will place the recipe in a task queue.

```shell
$ newslynx api recipes cook id=<id>
```

Alternatively, run the Recipe, passing in arbitrary runtime options, and stream it's output:

**NOTE** Will not execute the SousChef's ``load`` method.

```shell
$ newslynx api recipes cook id=<id> --passthrough **options
```

##### Development

Pass runtime options to `{{ slug }}` and stream output.

**NOTE** Will not execute the SousChef's `load` method.

```shell
$ newslynx sc-run {{ filepath }} option=value1
```

Alternatively pass in a recipe file

```shell
$ newslynx sc-run {{ filepath }} --recipe=recipe.yaml
```

#### Options


In addition to default recipe options, `{{ slug }}` also accepts the following


{% for name, params in options.iteritems() %}
{% if name not in default_options %}
- `{{ name }}`
{% if params.help.description is defined %}
\t* {{ params.help.description }}
{% endif %}
{% if params.required is defined %}
\t* **Required**
{% endif %}
\t* Should be rendered with a `{{params.input_type}}` form.
{% if params.input_options is defined %}
\t* Choose from:
{% for o in params.input_options %}
\t\t- `{{ o }}`
{% endfor %}
{% endif %}
\t* Accepts inputs of type:
{% for t in params.value_types %}
\t\t- `{{ t }}`
{% endfor %}
{% if params.default is defined %}
\t* Defaults to `{{params.default}}`
{% endif %}
{% if params.help.link is defined %}
\t* More details on this option can be found [here]({{ params.help.link  }})
{% endif %}
{% endif %}
{% endfor %}
""")

SC_METRICS_TMPL = Template("""
{% if metrics is defined %}
#### Metrics


`{{ slug }}` generates the following Metrics


{% for name, params in metrics.iteritems() %}
- `{{ name }}`
{% if params.description is defined %}
\t* {{ params.description }}
{% endif %}
\t* Display name: `{{ params.display_name }}`
{% if params.faceted is defined and params.faceted %}
\t* This is a **faceted** metric.
{% endif %}
{% if params.type == 'computed' %}
\t* This is a **computed** metric with the formula:
\t\t- {{ params.formula }}
{% else %}
\t* Type: `{{ params.type }}`
{% endif %}
{% if params.content_levels is defined and params.content_levels|length > 0 %}
\t* Content Levels:
{% for l in params.content_levels %}
\t\t- `{{ l }}`
{% endfor %}
{% endif %}
{% if params.org_levels is defined and params.org_levels|length > 0 %}
\t* Org Levels:
{% for l in params.org_levels %}
\t\t- `{{ l }}`
{% endfor %}
{% endif %}
{% endfor %}
{% endif %}
""")


def create(sc, fp, format='md'):
    """
    Create documentation for a SousChef from it's configurations.
    """
    try:
        sc['filepath'] = fp
        sc['default_options'] = sous_chef_schema.SOUS_CHEF_DEFAULT_OPTIONS.keys()
        opts = SC_OPTS_TMPL.render(**sc).strip().replace('\n\n', '\n')
        metrics = SC_METRICS_TMPL.render(**sc).strip().replace('\n\n', '\n')
        content = "\n{}\n\n{}\n".format(opts, metrics)
        return doc.convert(content, 'md', format)

    except:
        msg = """
        Documentation for Sous Chef {slug} located at {0}
        failed to generate for the following reason:
        {1}
        """.format(fp, format_exc(), **sc)
        raise SousChefDocError(msg)
