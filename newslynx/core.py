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
# from werkzeug.contrib.cache import RedisCache
from embedly import Embedly
import bitly_api

from newslynx import settings

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
db = SQLAlchemy(app, session_options={'query_cls': SearchQuery})

# session for interactions outside of app context.
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
db_session = scoped_session(sessionmaker(bind=engine))

# migrations
migrate = Migrate(app, db)

# Caching Layer
# cache = RedisCache()

# Migration
migrate = Migrate(app, db)

# gzip compression
Compress(app)

# Bitly
bitly_api = bitly_api.Connection(
    access_token=settings.BITLY_API_KEY)

# Embedly
embedly_api = Embedly(settings.EMBEDLY_API_KEY)
