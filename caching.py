class Cache:

    def __init__(self, path):
        self.path = path

    def cache(self, f):
        return f

    def save(self):
        pass