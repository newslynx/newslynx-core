

def get_table_columns(obj, incl=[]):
    """ Get the column names for a Table object"""
    cols = [str(c).split('.')[-1] for c in obj.__table__.columns]
    return cols + incl


def fetch_by_id_or_field(model, field, value, org_id=None):
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
        if not org_id:
            return model.query.filter_by(id=value).first()
        else:
            return model.query.filter_by(id=value, org_id=org_id).first()
    else:
        f = getattr(model, field)
        if not org_id:
            return model.query.filter(f == value).first()

        else:
            return model.query.filter(f == value)\
                        .filter_by(org_id=org_id)\
                        .first()


def split_meta(obj, cols):
    """
    Split out meta fields from core columns.
    """
    meta = obj.pop('meta', {})
    for k in obj.keys():
        if k not in cols:
            meta[k] = obj.pop(k)
    obj['meta'] = meta
    return obj
