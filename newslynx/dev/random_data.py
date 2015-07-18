import uuid
import hashlib
from datetime import datetime, timedelta
import random
from random import choice
from string import letters
import copy

from faker import Faker

from newslynx import settings
from newslynx.init import (
    load_default_recipes, load_default_tags,
    load_sous_chefs)
from newslynx.models import *
from newslynx.models import recipe_schema
from newslynx.core import db_session
from newslynx.lib import dates
from newslynx.lib.serialize import obj_to_json
from newslynx.constants import *
from newslynx.exc import RecipeSchemaError
from newslynx.util import here
from newslynx.tasks import rollup_metric

# fake factory
fake = Faker()

fixtures_dir = here(__file__, 'fixtures')
thumbnail = open('{}/thumbnail.txt'.format(fixtures_dir)).read()
IMG_URL = 'https://www.propublica.org/images/ngen/gypsy_og_image/20150520-group-home-hearing-1200x630.jpg'

IMPACT_TAG_NAMES = ['Media pickup', 'Media social share',
                    'Indv. social share', 'Comm. social share']
SUBJECT_TAG_NAMES = ['Environment', 'Money & politics', 'Government', 'Health']


AUTHORS = ['Michael Keller', 'Brian Abelson', 'Merlynne Jones']

# a lookup of letters to their number
letters_to_int = dict(zip(list(set(letters.lower())), range(1,27)))

def random_date(n1, n2):
    dt = datetime.utcnow() - timedelta(days=choice(range(n1, n2)))
    dt += timedelta(hours=random_int(0, 24))
    return dt


def random_color():
    r = lambda: random.randint(0, 255)
    return '#%02X%02X%02X' % (r(), r(), r())


def random_authors(n):
    return [fake.name() for _ in range(1, choice(range(2, n)))]


def random_text(n):
    return fake.lorem()[:n]


def random_bool():
    return choice([True, False])


def random_int(n1, n2):
    return choice(range(n1, n2))


def random_percentage(n1, n2):
    return (choice(range(n1, n2, 1)) / 100.0) * 100.0


def random_url(scheme="http", ext=None):
    u = "{}://example.com/{}".format(scheme, uuid.uuid1())
    if ext:
        return "{}.{}".format(u, ext)
    return u


def random_email():
    n = fake.name().split(' ')[0].lower()
    return "{}@example.com".format(n)


def random_hash():
    return hashlib.md5(str(uuid.uuid1())).hexdigest()

def str_to_num(name):
    num = 0
    for c in name.lower():
        if c in letters_to_int:
            num += letters_to_int[c]
    return num


# GENERATORS #


# USER
def gen_user():
    u = User(
        name=fake.name(),
        email=random_email(),
        admin=True,
        password=random_text(10),
        created=random_date(1, 10))
    db_session.add(u)
    db_session.commit()
    return u


# Org
def gen_org(users):
    o = Org(name=fake.company(), timezone='America/New_York', domains=['example.com', 'blog.example.com'])
    o.users.extend(users)
    db_session.add(o)
    db_session.commit()
    return o


# Recipe
def gen_built_in_recipes(org):
    recipes = []
    metrics = []
    u = choice(org.users)
    # add default recipes
    for recipe in load_default_recipes():
        sous_chef_slug = recipe.pop('sous_chef')
        if not sous_chef_slug:
            raise RecipeSchemaError(
                'Default recipe "{}" is missing a "sous_chef" slug.'
                .format(recipe.get('name', '')))
        sc = SousChef.query\
            .filter_by(slug=sous_chef_slug)\
            .first()
        if not sc:
            raise RecipeSchemaError(
                '"{}" is not a valid SousChef slug or the SousChef does not yet exist.'
                .format(sous_chef_slug))
        recipe = recipe_schema.validate(recipe, sc.to_dict())
        recipe['user_id'] = u.id
        recipe['org_id'] = org.id
        r = Recipe(sc, **recipe)
        db_session.add(r)
        db_session.commit()
        recipes.append(r)

        # if the recipe creates metrics add them in here.
        if 'metrics' in sc.creates:
            for name, params in sc.metrics.items():
                m = Metric(
                    name=name,
                    recipe_id=r.id,
                    org_id=org.id,
                    **params)
                metrics.append(m)
                db_session.add(m)
                db_session.commit()
    return recipes, metrics


# Tags
def gen_impact_tags(org, n_impact_tags):
    impact_tags = []
    # default
    for tag in load_default_tags():
        if tag['type'] == 'impact':
            tag['org_id'] = org.id
            t = db_session.query(Tag)\
                .filter_by(org_id=org.id, name=tag['name'])\
                .first()
            if not t:
                t = Tag(**tag)
                db_session.add(t)
                db_session.commit()
                impact_tags.append(t)
    return impact_tags


# TAGS
def gen_subject_tags(org, n_subject_tags):
    subject_tags = []
    for tag in load_default_tags():
        if tag['type'] == 'subject':
            tag['org_id'] = org.id
            t = db_session.query(Tag)\
                .filter_by(org_id=org.id, name=tag['name'])\
                .first()
            if not t:
                t = Tag(**tag)
                db_session.add(t)
                db_session.commit()
            subject_tags.append(t)
    return subject_tags


# AUTHORS
def gen_authors(org):
    authors = []
    for name in AUTHORS:
        c = Author(
            org_id=org.id,
            name=name,
            created=random_date(100, 200))
        db_session.add(c)
        db_session.commit()
        authors.append(c)
    return authors


# EVENTS
def gen_events(org, recipes, impact_tags, content_items, n_events):
    events = []
    for i in xrange(n_events):
        r = choice([r for r in recipes if r.sous_chef.creates == 'events'])
        authors = random_authors(4)

        e = Event(
            org_id=org.id,
            status=r.to_dict().get('options', {}).get('event_status', 'pending'),
            recipe_id=r.id,
            source_id="{}:{}".format(r.slug, str(uuid.uuid1())),
            title=random_text(20),
            description=random_text(100),
            url=random_url(),
            img_url=IMG_URL,
            thumbnail=thumbnail,
            body=random_text(500),
            created=random_date(10, 100),
            updated=random_date(1, 9),
            authors=authors,
            provenance='recipe')

        if 'twitter' in r.slug:
            e.meta = {'followers': random_int(1, 10000)}

        t = choice(impact_tags)
        e.tags.append(t)
        c = choice(content_items)
        e.content_items.append(c)
        db_session.add(e)
        events.append(e)
    db_session.commit()
    return e


# content_items
def gen_content_item(org, recipes, subject_tags, authors):

    r = choice([r for r in recipes if r.sous_chef.creates=='content'])
    st = choice(subject_tags)
    c = choice(authors)
    provenance = choice(CONTENT_ITEM_PROVENANCES)

    t = ContentItem(
        org_id=org.id,
        recipe_id=r.id,
        url=random_url(),
        type=choice(CONTENT_ITEM_TYPES),
        site_name=choice(["ProPalpatine", "Tatooine Times"]),
        favicon="http://propublica.org/favicon.ico",
        provenance=provenance,
        created=random_date(10, 100),
        updated=random_date(1, 9),
        domain='example.com',
        title=random_text(20),
        description=random_text(100),
        body=random_text(500),
        img_url=IMG_URL,
        thumbnail=thumbnail)

    if provenance == 'manual':
        t.recipe_id = None

    t.tags.append(st)
    t.authors.append(c)
    db_session.add(t)
    db_session.commit()
    return t


def gen_content_metric_timeseries(org, content_items, metrics, n_content_item_timeseries_metrics=1000):
    # all
    date_list = []
    start = dates.now() - timedelta(days=7)
    for hour in range(1, (7*24)+1):
        date_list.append(start + timedelta(hours=hour))

    for c in content_items:
        last_values = {}
        for i, d in enumerate(date_list):
            _metrics = {}
            for m in metrics:
                if 'timeseries' in m.content_levels:
                    if m.type=='cumulative':
                        if m.name not in last_values:
                            last_values[m.name] = 0
                        last_values[m.name] += random_int(0, 100)
                        _metrics[m.name] = copy.copy(last_values[m.name])
                    else:
                        _metrics[m.name] = random_int(1, 1000)

            cmd_kwargs = {
                'org_id': org.id,
                'content_item_id': c.id,
                'datetime': d.isoformat(),
                'metrics': obj_to_json(_metrics)
            }
            # upsert command
            cmd = """SELECT upsert_content_metric_timeseries(
                        {org_id},
                        {content_item_id},
                        '{datetime}',
                        '{metrics}');
                   """.format(**cmd_kwargs)
            db_session.execute(cmd)
    db_session.commit()



def gen_org_metric_timeseries(org, metrics, n_org_timeseries_metrics=1000):
    for _ in xrange(n_org_timeseries_metrics):
        _metrics = {}
        for m in metrics:
            if 'timeseries' in m.org_levels:
                if m.type != 'cumulative':
                    _metrics[m.name] = random_int(1, 1000)
                else:
                    _metrics[m.name] = _ * random_int(2, 10)

        cmd_kwargs = {
            'org_id': org.id,
            'datetime': dates.floor(random_date(1, 120), unit='hour', value=1),
            'metrics': obj_to_json(_metrics)
        }
        # upsert command
        cmd = """SELECT upsert_org_metric_timeseries(
                    {org_id},
                    '{datetime}',
                    '{metrics}');
               """.format(**cmd_kwargs)
        db_session.execute(cmd)
    db_session.commit()


def gen_content_metric_summaries(org, content_items, metrics):

    for c in content_items:
        _metrics = {}
        for m in metrics:
            if 'summary' in m.content_levels and not 'timeseries' in m.content_levels:
                if not m.faceted:
                    _metrics[m.name] = random_int(1, 1000)
                else:
                    _metrics[m.name] = [
                        {
                            'facet': 'google.com',
                            'value': random_int(1, 1000),
                        },
                        {
                            'facet': 'twitter.com',
                            'value': random_int(1, 1000)
                        },
                        {
                            'facet': 'facebook.com',
                            'value': random_int(1, 1000)
                        }
                    ]
        cmd_kwargs = {
            'org_id': org.id,
            'content_item_id': c.id,
            'metrics': obj_to_json(_metrics)
        }
        # upsert command
        cmd = """SELECT upsert_content_metric_summary(
                    {org_id},
                    {content_item_id},
                    '{metrics}');
               """.format(**cmd_kwargs)
        db_session.execute(cmd)
    db_session.commit()


def main(
        n_users=2,
        n_event_recipes=10,
        n_content_item_recipes=10,
        n_subject_tags=10,
        n_impact_tags=10,
        n_events=500,
        n_content_item_timeseries_metrics=10000,
        n_org_timeseries_metrics=10000,
        n_content_items=50,
        verbose=True):

    # top level content_items
    admin = db_session.query(User).filter_by(email=settings.SUPER_USER_EMAIL).first()
    users = [gen_user() for _ in xrange(n_users)] + [admin]
    org = gen_org(users)
    impact_tags = gen_impact_tags(org, n_subject_tags)
    subject_tags = gen_subject_tags(org, n_impact_tags)
    authors = gen_authors(org)
    recipes, metrics = gen_built_in_recipes(org)

    # generate content_items + metrics
    if verbose:
        print "generating {} content items".format(n_content_items)
    content_items = []
    for i in xrange(n_content_items):
        content_item = gen_content_item(org, recipes, subject_tags, authors)
        content_items.append(content_item)

    if verbose:
        print "generating {} events".format(n_events)

    if verbose:
        print "generating {} content item timeseries metrics"\
            .format(n_content_item_timeseries_metrics)

    gen_content_metric_timeseries(
        org,
        content_items,
        metrics,
        n_content_item_timeseries_metrics)

    if verbose:
        print "generating {} org timeseries metrics"\
            .format(n_org_timeseries_metrics)

    gen_org_metric_timeseries(
        org,
        metrics,
        n_org_timeseries_metrics)

    if verbose:
        print "generating {} events"\
            .format(n_events)

    # generate events
    gen_events(org, recipes, impact_tags, content_items, n_events)
    db_session.commit()

    # generate content summaries
    gen_content_metric_summaries(org, content_items, metrics)

    # rollup metrics
    if verbose:
        print "rolling up metrics"
    rollup_metric.content_timeseries_to_summary(org)
    rollup_metric.event_tags_to_summary(org)


def run(**kw):
    """
    A wrapper for random data generator which rollsback on error.
    """
    # try:
    main(**kw)
    # except Exception as e:
    #     db_session.rollback()
    #     raise e
