"""
Objects that we need access to throughout the project.
"""
from traceback import format_exc

from sqlalchemy import func, cast
from sqlalchemy_searchable import vectorizer
from sqlalchemy.dialects.postgresql import ARRAY, JSON, TEXT, ENUM
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy, BaseQuery
from sqlalchemy_searchable import make_searchable, SearchQueryMixin
from flask.ext.migrate import Migrate
from flask.ext.compress import Compress
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import redis
from rq import Queue
from embedly import Embedly
import bitly_api as bitly

from newslynx import settings
from newslynx.constants import TASK_QUEUE_NAMES
from newslynx.exc import ConfigError

# import logs module to set handler
from newslynx import logs



# Flask Application
app = Flask(__name__)

app.config.from_object(settings)


# search
class SearchQuery(BaseQuery, SearchQueryMixin):

    """
    A special class for enabling search on a table.
    """
    pass


@vectorizer(ARRAY)
def array_vectorizer(column):
    return func.array_to_string(column, ' ')


@vectorizer(JSON)
def json_vectorizer(column):
    return cast(column, TEXT)


@vectorizer(ENUM)
def enum_vectorizer(column):
    return cast(column, TEXT)


# make the db searchable
make_searchable()

# Database
try:
    db = SQLAlchemy(app, session_options={'query_cls': SearchQuery})
    db.engine.pool._use_threadlocal = True
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI,
                           strategy='threadlocal',
                           max_overflow=settings.SQLALCHEMY_POOL_MAX_OVERFLOW,
                           pool_size=settings.SQLALCHEMY_POOL_SIZE
                           )

    # session for interactions outside of app context.
    def gen_session():
        return scoped_session(sessionmaker(bind=engine))

except Exception as e:
    if not settings.TESTING:
        raise ConfigError(format_exc())
    else:
        pass

# redis connection
rds = redis.from_url(settings.REDIS_URL)

# task queues
queues = {k: Queue(k, connection=rds) for k in TASK_QUEUE_NAMES}

# migrations
migrate = Migrate(app, db)

# gzip compression
Compress(app)

# optional bitly api for shortening
if settings.BITLY_ENABLED:
    bitly_api = bitly.Connection(
        access_token=settings.BITLY_ACCESS_TOKEN)

# optional embedly api for shortening
if settings.EMBEDLY_ENABLED:
    embedly_api = Embedly(settings.EMBEDLY_API_KEY)
