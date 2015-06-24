from newslynx.client import API

org = 1
api = API(org=1)


for res in api.sql.execute('SELECT * FROM users'):
    assert(isinstance(res, dict))

for res in api.sql.execute("UPDATE users set name = name || '1' "):
    assert(isinstance(res, dict))
    assert(res['success'])
