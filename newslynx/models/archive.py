

class Archive(object):
    """
    A generic class to inherit from.
    """

    def directory(self):

    def key(self, **kw):
        return self.kw.get('id')

    def format(self, **kw):
        return 

    def get(self, fp, **kw):
        pass

    def put(self, fp, **kw):
        pass

    def exists(self, fp, **kw):
        pass

    def age(self, fp, **kw):
        pass

    def _exec(self, cmd, **kw)
        fp = self.format(key=self.key, **kw)


