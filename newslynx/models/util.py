
def get_table_columns(obj, incl=[]):
    """ Get the column names for a Table object"""
    cols = [str(c).split('.')[-1] for c in obj.__table__.columns]
    return cols + incl


def fetch_by_id_or_field(model, field, value, transform=None,
                         org_id=None,
                         user_id=None,
                         level=None):
    """
    Fetch a model by it's id or a string fields
    """

    # check for int / str
    try:
        value = int(value)
        is_int = True
    except:
        is_int = False

    if is_int:

        if user_id and org_id and level:
            return model.query\
                .filter_by(id=value, org_id=org_id, user_id=user_id, level=level)\
                .first()

        elif org_id:
            return model.query\
                .filter_by(id=value, org_id=org_id)\
                .first()
        return model.query\
            .filter_by(id=value)\
            .first()

    else:
        f = getattr(model, field)
        if transform == 'upper':
            value = value.upper()
        elif transform == 'lower':
            value = value.lower()
        q = model.query.filter(f == value)
        if user_id and org_id and level:
            return q\
                .filter_by(org_id=org_id, user_id=user_id, level=level)\
                .first()
        elif org_id:
            return q\
                .filter_by(org_id=org_id)\
                .first()
        return q.first()
