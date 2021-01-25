
import itertools
import inspect
import shelve

class CachedFunction:

    def __init__(self, cache, function):
        self.cache = cache
        self.non_lazy = NonLazyFunction(function).get_wrapper()

        filepath   = function.__globals__['__file__']
        name       = function.__qualname__
        self.function_id = filepath + "/" + name

    def get_wrapper(self):
        def wrapper(*args, **kwargs):
            if self.cache.has(self.function_id, args, kwargs):
                return self.cache.get(self.function_id, args, kwargs)
            else:
                result = self.non_lazy(*args, **kwargs)
                self.cache.set(self.function_id, args, kwargs, result)
                return result
        return wrapper


class StateModifyingFunction:

    def __init__(self, method):
        self.method = method

    def get_wrapper(self):
        def wrapper(*args, **kwargs):
            OBJECT_TRACKER.add(
                args[0],
                self.method,
                args,
                kwargs
            )
        return wrapper


class NonLazyFunction:

    def __init__(self, function):
        self.tracker = OBJECT_TRACKER
        self.function = function

    def get_wrapper(self):
        def wrapper(*args, **kwargs):
            for item in itertools.chain(args, kwargs.values()):
                self.tracker.sync(item)
            return self.function(*args, **kwargs)
        return wrapper


class ObjectState:

    def __init__(self, klass):
        try:
            filepath = inspect.getfile(klass)
        except TypeError:
            filepath = ""
        name = klass.__qualname__
        self.subkey = filepath + "/" + name
        self.calls = []

    def get_subkey(self):
        return self.subkey

    def sync(self):
        for (method, args, kwargs) in self.calls:
            method(*args, *kwargs)
        self.calls = []

    def add(self, method, args, kwargs):
        self.calls.append((method, args, kwargs))
        self.subkey += method.__name__
        for arg in args:
            self.subkey += get_subkey(arg)
        for keyword in kwargs:
            self.subkey += keyword
            self.subkey += get_subkey(kwargs[keyword])


class ObjectTracker:

    def __init__(self):
        self.tracked = {}

    def sync(self, item):
        if id(item) in self.tracked:
            self.tracked[id(item)].sync()

    def add(self, item, method, args, kwargs):
        key = id(item)
        if key not in self.tracked:
            self.track(item)
        self.tracked[key].add(method, args, kwargs)

    def has(self, item):
        return id(item) in self.tracked

    def track(self, item):
        self.tracked[id(item)] = ObjectState(type(item))

    def get_subkey(self, item):
        return self.tracked[id(item)].get_subkey()


class Cache:

    def __init__(self, filepath):
        self.shelf = shelve.open(filepath)
    
    def cached(self, function):
        return CachedFunction(self, function).get_wrapper()

    def has(self, function_id, args, kwargs):
        key = CacheKey(function_id, args, kwargs)
        return key.serialize() in self.shelf

    def get(self, function_id, args, kwargs):
        key = CacheKey(function_id, args, kwargs)
        return self.shelf[key.serialize()]

    def set(self, function_id, args, kwargs, value):
        key = CacheKey(function_id, args, kwargs)
        self.shelf[key.serialize()] = value


class CacheKey:

    def __init__(self, function_id, args, kwargs):
        self.serialized  = function_id
        for arg in args:
            self.serialized += get_subkey(arg)
        for keyword in kwargs:
            self.serialized += keyword
            self.serialized += get_subkey(kwargs[keyword])

    def serialize(self):
        return self.serialized


def get_subkey(item):
    if type(item) in AUTO_CLASSES:
        if not OBJECT_TRACKER.has(item):
            OBJECT_TRACKER.track(item)
        return OBJECT_TRACKER.get_subkey(item)
    else:
        try:
            subkey = item.cache_signature
        except AttributeError:
            subkey = repr(item)
        return subkey


def auto(klass):
    AUTO_CLASSES.append(klass)
    return klass


def state_modifying(method):
    return StateModifyingFunction(method).get_wrapper()


def nonlazy(method):
    return NonLazyFunction(method).get_wrapper()


AUTO_CLASSES = []
OBJECT_TRACKER = ObjectTracker()

cache = Cache("cache")

@auto
class Sum:

    def __init__(self, value=0):
        self.value = value

    @state_modifying
    def add(self, term):
        self.value += term

    @cache.cached
    def get_value(self):
        return self.value


if __name__ == "__main__":
    s = Sum()
    s.add(1)
    assert s.get_value() == 1