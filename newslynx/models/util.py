
def get_table_columns(obj):
    """ Get the column names for a Table object"""
    return [str(c).split('.')[-1] for c in obj.__table__.columns]
