import uuid
import hashlib
from datetime import datetime, timedelta
import random
from random import choice

from faker import Faker

from newslynx import settings
from newslynx.init import (
    load_default_recipes, load_default_tags,
    load_sous_chefs)
from newslynx.models import *
from newslynx.core import db_session
from newslynx.lib import dates
from newslynx.lib.serialize import obj_to_json
from newslynx.constants import *
from newslynx.exc import RecipeSchemaError

# fake factory
fake = Faker()


IMPACT_TAG_NAMES = ['Media pickup', 'Media social share',
                    'Indv. social share', 'Comm. social share']
SUBJECT_TAG_NAMES = ['Environment', 'Money & politics', 'Government', 'Health']


AUTHORS = ['Michael Keller', 'Brian Abelson', 'Merlynne Jones']

METRICS = [
    {
        'name': 'pageviews',
        'display_name': 'Pageviews',
        'level': 'content_item',
        'aggregation': 'sum',
        'timeseries': True,
        'cumulative': False,
        'faceted': False
    },
    {
        'name': 'time_on_homepage',
        'display_name': 'Time on homepage',
        'level': 'content_item',
        'aggregation': 'sum',
        'timeseries': True,
        'cumulative': False,
        'faceted': False
    },
    {
        'name': 'twitter_shares',
        'display_name': 'Twitter Shares',
        'level': 'content_item',
        'aggregation': 'sum',
        'timeseries': True,
        'cumulative': True,
        'faceted': False
    },
    {
        'name': 'external_pageviews',
        'display_name': 'External Pageviews',
        'level': 'content_item',
        'aggregation': 'sum',
        'timeseries': False,
        'cumulative': False,
        'faceted': False
    },
    {
        'name': 'pageviews_by_referrer',
        'display_name': 'Pageviews by Referrer',
        'level': 'content_item',
        'aggregation': 'sum',
        'timeseries': False,
        'cumulative': False,
        'faceted': True
    },
    {
        'name': 'facebook_page_likes',
        'display_name': 'Facebook Page Likes',
        'level': 'org',
        'aggregation': 'sum',
        'timeseries': True,
        'cumulative': True,
        'faceted': False
    },
    {
        'name': 'twitter_followers',
        'display_name': 'Twitter Followers',
        'level': 'org',
        'aggregation': 'sum',
        'timeseries': True,
        'cumulative': True,
        'faceted': False

    }
]


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


def random_meta():
    meta = {
        'followers': choice(range(1, 100)),
        'address': fake.street_address(),
        'text': fake.lorem()[:10]
    }
    keys = meta.keys()
    for i in range(0, choice(range(0, len(keys)))):
        k = keys[i]
        meta.pop(k)
    return meta


# GENERATORS #


# USER
def gen_admin_user():
    u = User.query.filter_by(email=settings.ADMIN_EMAIL).first()
    if not u:
        u = User(email=settings.ADMIN_EMAIL,
                 password=settings.ADMIN_PASSWORD,
                 name=settings.ADMIN_USER,
                 admin=True)
        db_session.add(u)
        db_session.commit()
    return u


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
    o = Org(name=fake.company(), timezone='America/New_York')
    o.users.extend(users)
    db_session.add(o)
    db_session.commit()
    return o


def get_sous_chefs():
    sous_chefs = []
    for sc in load_sous_chefs():
        s = db_session.query(SousChef)\
            .filter_by(slug=sc['slug'])\
            .first()
        if not s:
            s = SousChef(**sc)
            db_session.add(s)
            db_session.commit()
        sous_chefs.append(s)
    return sous_chefs


# Recipe
def gen_built_in_recipes(org):
    recipes = []
    u = choice(org.users)
    # add default recipes
    for recipe in load_default_recipes():
        recipe['user_id'] = u.id
        recipe['org_id'] = org.id
        recipe['status'] = 'uninitialized'
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
        r = db_session.query(Recipe)\
            .filter_by(org_id=org.id, slug=recipe['slug'])\
            .first()
        if not r:

            r = Recipe(sc, **recipe)
            db_session.add(r)
            db_session.commit()
        recipes.append(r)
    return recipes


# Tags
def gen_impact_tags(org, n_impact_tags):

    # random
    impact_tags = []
    for _ in xrange(n_impact_tags):
        t = Tag(
            org_id=org.id,
            name=random_text(20) + str(random_int(1, 100)),
            color=random_color(),
            type='impact',
            category=choice(IMPACT_TAG_CATEGORIES),
            level=choice(IMPACT_TAG_LEVELS))
        db_session.add(t)
        db_session.commit()
        impact_tags.append(t)

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
    return impact_tags


# TAGS
def gen_subject_tags(org, n_subject_tags):
    subject_tags = []
    for _ in xrange(n_subject_tags):
        t = Tag(
            org_id=org.id,
            name=random_text(20) + str(random_int(1, 100)),
            color=random_color(),
            type='subject')
        db_session.add(t)
        db_session.commit()
        subject_tags.append(t)

    # default
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
            impact_tags.append(t)
    return subject_tags


# AUTHORS
def gen_authors(org):
    authors = []
    for name in AUTHORS:
        c = Author(
            org_id=org.id,
            name=name,
            created=random_date(100, 200),
            meta=random_meta())
        db_session.add(c)
        db_session.commit()
        authors.append(c)
    return authors


# EVENTS
def gen_events(org, recipes, impact_tags, content_items, n_events):
    events = []
    for i in xrange(n_events):
        status = choice(EVENT_STATUSES)
        provenance = choice(EVENT_PROVENANCES)
        r = choice(recipes)
        authors = random_authors(4)

        if provenance == 'manual':
            prefix = 'manual'
        else:
            prefix = r.slug

        e = Event(
            org_id=org.id,
            recipe_id=r.id,
            source_id="{}:{}".format(prefix, str(uuid.uuid1())),
            title=random_text(20),
            description=random_text(100),
            url=random_url(),
            img_url=random_url(ext='png'),
            body=random_text(500),
            created=random_date(10, 100),
            updated=random_date(1, 9),
            authors=authors,
            status=status,
            provenance=provenance,
            meta=random_meta())

        if status == 'approved':
            e.tags.append(choice(impact_tags))
            e.content_items.append(choice(content_items))

        if provenance == 'manual':
            e.recipe_id = None

        db_session.add(e)
        events.append(e)
    db_session.commit()
    return e


# content_items
def gen_content_item(org, recipes, subject_tags, authors):

    r = choice(recipes)
    st = choice(subject_tags)
    c = choice(authors)
    provenance = choice(CONTENT_ITEM_PROVENANCES)

    t = ContentItem(
        org_id=org.id,
        recipe_id=r.id,
        url=random_url(),
        type=choice(CONTENT_ITEM_TYPES),
        provenance=provenance,
        created=random_date(10, 100),
        updated=random_date(1, 9),
        domain='example.com',
        title=random_text(20),
        description=random_text(100),
        body=random_text(500),
        img_url=random_url(ext='jpg'),
        meta=random_meta())

    if provenance == 'manual':
        t.recipe_id = None

    t.tags.append(st)
    t.authors.append(c)
    db_session.add(t)
    db_session.commit()
    return t

# METRICS


def gen_metrics(org, recipes):
    _metrics = []
    for metric in METRICS:
        r = choice(recipes)

        m = Metric(
            org_id=org.id,
            recipe_id=r.id,
            **metric)
        db_session.add(m)
        _metrics.append(m)
    db_session.commit()
    return _metrics


def gen_content_metric_timeseries(org, content_items, metrics, n_content_item_timeseries_metrics=1000):
    for _ in xrange(n_content_item_timeseries_metrics):
        _metrics = {}
        for m in metrics:
            if m.level == 'content_item':
                _metrics[m.name] = random_int(1, 1000)

        cmd_kwargs = {
            'org_id': org.id,
            'content_item_id': choice(content_items).id,
            'datetime': dates.floor(random_date(1, 7), unit='hour', value=1),
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
            if m.level == 'org':
                _metrics[m.name] = random_int(1, 120)

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
    admin = gen_admin_user()
    users = [gen_user() for _ in xrange(n_users)] + [admin]
    org = gen_org(users)
    impact_tags = gen_impact_tags(org, n_subject_tags)
    subject_tags = gen_subject_tags(org, n_impact_tags)
    authors = gen_authors(org)
    sous_chefs = get_sous_chefs()
    recipes = gen_built_in_recipes(org)

    # generate content_items + metrics
    if verbose:
        print "generating {} content items".format(n_content_items)
    content_items = []
    for i in xrange(n_content_items):
        content_item = gen_content_item(org, recipes, subject_tags, authors)
        content_items.append(content_item)

    if verbose:
        print "generating {} events".format(n_events)

    metrics = gen_metrics(org, recipes)

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


def run(**kw):
    """
    A wrapper for random data generator which rollsback on error.
    """
    # try:
    main(**kw)
    # except Exception as e:
    #     db_session.rollback()
    #     raise e
