import shelve

class Cache:

    def __init__(self, path):
        self.path = path
        self.shelf = shelve.open(path)

    def cache(self, f):
        filepath = f.__globals__['__file__']
        name     = f.__qualname__

        def wrapper(*args, **kwargs):
            key = CacheKey()
            key.append(filepath)
            key.append(name)
            key.append(str(len(args)))
            key.append(str(len(kwargs)))

            for argument in args:
                argument_id = get_cache_id(argument)
                key.append(argument_id)

            for keyword in kwargs:
                argument_id = get_cache_id(kwargs[keyword])
                key.append(keyword)
                key.append(argument_id)

            serialized_key = key.serialize()
            if serialized_key in self.shelf:
                result = self.shelf[serialized_key]
            else:
                result = f(*args, **kwargs)
                self.shelf[serialized_key] = result
            return result

        return wrapper

    def save(self):
        self.shelf.sync()

    def close(self):
        self.shelf.close()

    def __del__(self):
        self.close()


class CacheKey:

    def __init__(self):
        self.value = ""

    def append(self, cache_id):
        self.value += cache_id

    def serialize(self):
        return self.value


def get_cache_id(argument):
    try:
        argument_id = argument.cache_id
    except AttributeError:
        argument_id = repr(argument)
    return argument_id
