from newslynx.models import Event
print [str(c).split('.') for c in Event.__table__.columns]

events = Event.query.search('ali').all()
print [e.to_dict() for e in events]