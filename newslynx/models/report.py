from sqlalchemy.dialects.postgresql import JSON, ARRAY

from slugify import slugify

from newslynx.core import db, rds
from newslynx.lib import dates
from newslynx import settings
from newslynx.settings import (
    REPORTS_MIN_DATE_UNIT,
    REPORTS_MIN_DATE_VALUE,
    REPORTS_TEMPLATE_FILE_FORMAT,
    REPORTS_CURRENT_FILE_FORMAT,
    REPORTS_VERSION_FILE_FORMAT,
    REPORTS_DATA_FILE_FORMAT,
    REPORTS_DATA_FORMATS,
    REPORTS_TEMPLATE_FORMATS
)


class Report(db.Model):

    __tablename__ = 'reports'
    __module__ = 'newslynx.models.report'

    id = db.Column(db.Integer, unique=True, index=True, primary_key=True)

    org_id = db.Column(
        db.Integer, db.ForeignKey('orgs.id'), index=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), index=True)

    recipe_id = db.Column(
        db.Integer, db.ForeignKey('recipes.id'), index=True)

    # report metadata
    name = db.Column(db.Text)
    description = db.Column(db.Text)
    slug = db.Column(db.Text, index=True)
    created = db.Column(db.DateTime(timezone=True))
    updated = db.Column(
        db.DateTime(timezone=True), onupdate=dates.now, default=dates.now)

    # access
    public = db.Column(db.Boolean, index=True)
    archived = db.Column(db.Boolean, index=True)

    # template metadata
    template = db.Column(JSON)

    def __init__(self, **kw):
        unit = settings.REPORTS_MIN_DATE_UNIT,
        value = settings.REPORTS_MIN_DATE_VALUE

        # relations
        self.recipe_id = kw.get('recipe_id')
        self.sous_chef_id = kw.get('sous_chef_id')
        self.user_id = kw.get('user_id')
        self.org_id = kw.get('org_id')

        # meta data
        self.name = kw.get('name')
        self.slug = slugify(kw.get('slug', kw['name']))
        self.description = kw.get('description')
        self.created = dates.floor(
            kw.get('created', dates.now(), unit=unit, value=value))

        # template
        self.template = kw.get('template',  {})

        # storage
        self.archived = kw.get('archived', False)

        # access
        self.public = kw.get('public', False)

    __table_args__ = (
        db.UniqueConstraint('org_id', 'slug'),
    )

    def to_dict(self, **kw):
        """

        """
        incl_sous_chef = kw.get('incl_sous_chef', True)
        incl_recipes = kw.get('incl_recipe', True)
        incl_org = kw.get('incl_org', True)
        incl_user = kw.get('incl_user', True)
        incl_ymdhms = kw.get('incl_ymdhms', False)

        d = {
            'id': self.id,
            'org': self.org.slug,
            'org_id': self.org_id,
            'user_id': self.user_id,
            'recipe_id': self.recipe_id,
            'sous_chef': self.sous_chef.slug,
            'name': self.name,
            'slug': self.slug,
            'created': self.created,
            'updated': self.updated,
            'template': self.template,
            'has_template': self.has_template,
            'can_render': self.can_render
        }
        if incl_sous_chef:
            d['sous_chef'] = self.sous_chef.to_dict()

        if incl_recipe:
            d['recipe'] = self.recipe

        if incl_ymdhms:
            d.update({
                'year': self.created.year,
                'hour': "%02d" % int(self.created.hour),
                'day': "%02d" % int(self.created.day),
                'month': "%02d" % int(self.created.month),
                'minute': "%02d" % int(self.created.minute),
                'second': "%02d" % int(self.created.second)
            })
        return d

    # HELPERS

    @property
    def archive_dir(self):
        pass

    @property
    def has_template(self):
        return len(self.template.keys())

    @property
    def can_render(self):
        if self.has_template:
            return REPORTS_TEMPLATE_FORMATS[self.template['format']]
        return REPORTS_DATA_FORMATS[self.data_format]

    @property
    def data_format(self):
        return settings.REPORTS_DATA_SERIALIZATION_FORMAT

    # filepaths
    @property
    def data_filepath(self):
        """
        Load data in from redis.
        """
        return REPORTS_DATA_FILE_FORMAT.fomat(
            format = self.data_format,
            **self.to_dict('incl_ymdhms', True)
        )

    @property
    def template_filepath(self):
        if self.has_template:
            return REPORTS_TEMPLATE_FILE_FORMAT.format(**self.to_dict('incl_ymdhms', True))

    def current_filepath(self, format, **kw):
        return REPORTS_CURRENT_FILE_FORMAT.format(
            format=format, **self.to_dict('incl_ymdhms', True)
        )

    def versioned_filepath(self, format, **options):
        """
        Create a filename for a report.
        """
        p = obj_to_pickle(options)
        options_hash = str(md5(p).hexdigest())
        return REPORTS_VERSION_FILE_FORMAT.format(
            format=format, options_hash=options_hash,
            **self.to_dict('incl_ymdhms', True)
        )


    def __repr__(self):
        return "<Report %r / %r >" % (self.org_id, self.slug)
