import uuid
import hashlib
from datetime import datetime, timedelta
import random
import copy
from random import choice

from faker import Faker

from newslynx import settings
from newslynx.models import *
from newslynx.core import db_session
from newslynx.taxonomy import *


# fake factory
fake = Faker()


TAG_TYPES = ['subject', 'impact']
IMPACT_TAG_NAMES = ['Media pickup', 'Media social share',
                    'Indv. social share', 'Comm. social share']
SUBJECT_TAG_NAMES = ['Environment', 'Money & politics', 'Government', 'Health']

TASK_NAMES = [
    'twitter-domain-mentions',
    'google-analytics-trackbacks',
    'google-analytics-pageviews',
    'some-other-task',
    'another-task'
]

CREATORS = ['Michael Keller', 'Brian Abelson', 'Merlynne Jones']

METRICS = [
    {
        'name': 'pageviews',
        'category': 'performance',
        'level': 'thing',
        'timeseries': True,
        'cumulative': False
    },
    {
        'name': 'on_homepage',
        'category': 'promotion',
        'level': 'thing',
        'timeseries': True,
        'cumulative': False
    },
    {
        'name': 'twitter_shares',
        'category': 'performance',
        'level': 'thing',
        'timeseries': True,
        'cumulative': False
    },
    {
        'name': 'external_pageviews',
        'category': 'performance',
        'level': 'thing',
        'timeseries': False,
        'cumulative': False
    },
    {
        'name': 'pageviews_by_referrer__google_com',
        'category': 'performance',
        'level': 'thing',
        'timeseries': False,
        'cumulative': False
    },
    {
        'name': 'pageviews_by_referrer__reddit_com',
        'category': 'performance',
        'level': 'thing',
        'timeseries': False,
        'cumulative': False
    },
    {
        'name': 'facebook_page_likes',
        'category': 'performance',
        'level': 'organization',
        'timeseries': True,
        'cumulative': True
    }
]


def random_date(n1, n2):
    return datetime.utcnow() - timedelta(days=choice(range(n1, n2)))


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
    o = Organization(name=fake.company())
    o.users.extend(users)
    db_session.add(o)
    db_session.commit()
    return o


def gen_tasks():
    tasks = []
    for t in TASK_NAMES:
        t = Task(
            name=t,
            description=random_text(20),
            config=random_meta())
        db_session.add(t)
        tasks.append(t)
    return tasks


# Recipe
def gen_recipe(org, users, tasks):
    t = choice(tasks)
    r = Recipe(
        organization_id=org.id,
        task_id=t.id,
        name=random_text(10),
        description=random_text(20),
        config=random_meta(),
        created=random_date(1, 9),
        scheduled=random_bool(),
        interval=choice([None, random_int(60, 240)]),
        backoff=choice([None, random_int(1, 5)]),
        ttl=choice([None, random_int(400, 600)])
    )
    db_session.add(r)
    db_session.commit()
    return r


# Tags
def gen_impact_tags(org, n_impact_tags):
    impact_tags = []
    for _ in xrange(n_impact_tags):
        t = Tag(
            organization_id=org.id,
            name=random_text(10),
            color=random_color(),
            type='impact',
            category=choice(IMPACT_TAG_CATEGORIES),
            level=choice(IMPACT_TAG_LEVELS))
        db_session.add(t)
        db_session.commit()
        impact_tags.append(t)
    return impact_tags


# TAGS
def gen_subject_tags(org, n_subject_tags):
    subject_tags = []
    for _ in xrange(n_subject_tags):
        t = Tag(
            organization_id=org.id,
            name=random_text(10),
            color=random_color(),
            type='subject')
        db_session.add(t)
        db_session.commit()
        subject_tags.append(t)
    return subject_tags


# CREATORS
def gen_creators(org):
    creators = []
    for name in CREATORS:
        c = Creator(
            organization_id=org.id,
            name=name,
            created=random_date(100, 200),
            meta=random_meta())
        db_session.add(c)
        db_session.commit()
        creators.append(c)
    return creators


# EVENTS
def gen_events(org, recipes, impact_tags, things, n_events):
    events = []
    for i in xrange(n_events):
        status = choice(EVENT_STATUSES)
        r = choice(recipes)
        authors = random_authors(4)

        e = Event(
            organization_id=org.id,
            recipe_id=r.id,
            source_id=uuid.uuid1(),
            title=random_text(20),
            description=random_text(100),
            url=random_url(),
            img_url=random_url(ext='.jpg'),
            text=random_text(500),
            created=random_date(10, 100),
            updated=random_date(1, 9),
            authors=authors,
            status=status,
            meta=random_meta())

        if status == 'approved':
            e.tags.append(choice(impact_tags))
            e.things.append(choice(things))
        db_session.add(e)
        events.append(e)
    db_session.commit()
    return e


# THINGS
def gen_thing(org, recipes, subject_tags, creators):

    r = choice(recipes)
    st = choice(subject_tags)
    c = choice(creators)

    t = Thing(
        organization_id=org.id,
        recipe_id=r.id,
        url=random_url(),
        type=choice(THING_TYPES),
        created=random_date(10, 100),
        updated=random_date(1, 9),
        domain='example.com',
        title=random_text(20),
        byline='By {}'.format(c.name),
        description=random_text(100),
        text=random_text(500),
        img_url=random_url(ext='.jpg'),
        meta=random_meta())

    t.tags.append(st)
    t.creators.append(c)
    db_session.add(t)
    db_session.commit()
    return t

# METRICS


def gen_metrics(org, thing, recipe, metric, n=100):
    for i in xrange(n):

        if metric['cumulative']:
            value = i * 1.25
        else:
            value = random_int(10, 10000)

        if metric['timeseries']:
            created = datetime.utcnow() - timedelta(days=(n - i))
        else:
            created = None

        m = Metric(
            organization_id=org.id,
            recipe_id=recipe.id,
            thing_id=thing.id,
            value=value,
            created=created,
            meta=random_meta(),
            **metric)
        db_session.add(m)
    db_session.commit()


def main(
        n_users=2,
        n_event_recipes=10,
        n_thing_recipes=10,
        n_subject_tags=10,
        n_impact_tags=10,
        n_events=100,
        n_metrics_per_thing=20,
        n_things=10,
        verbose=True):

    # top level things
    admin = gen_admin_user()
    users = [gen_user() for _ in xrange(n_users)] + [admin]
    org = gen_org(users)
    impact_tags = gen_impact_tags(org, n_subject_tags)
    subject_tags = gen_subject_tags(org, n_impact_tags)
    creators = gen_creators(org)
    tasks = gen_tasks()

    # generate things + metrics
    thing_recipes = [gen_recipe(org, users, tasks) for _ in xrange(n_thing_recipes)]
    metric_recipes = [gen_recipe(org, users, tasks) for _ in range(len(METRICS))]

    things = []
    for i in xrange(n_things):

        thing = gen_thing(org, thing_recipes, subject_tags, creators)
        things.append(thing)
        for metric, recipe in zip(METRICS, metric_recipes):
            if not metric['timeseries']:
                n_metrics = 1
            else:
                n_metrics = copy.copy(n_metrics_per_thing)
            if verbose:
                print "generating {} {} for thing {} of {}"\
                    .format(n_metrics, metric['name'], i, n_things)

            gen_metrics(org, thing, recipe, metric, n_metrics)

    if verbose:
        print "generating {} events".format(n_events)

    # generate events
    event_recipes = [gen_recipe(org, users, tasks) for _ in xrange(n_event_recipes)]
    gen_events(org, event_recipes, impact_tags, things, n_events)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1].startswith('v'):
            verbose = True
    else:
        verbose = False
    main(verbose=verbose)
