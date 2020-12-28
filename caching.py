import shelve
import inspect

class Cache:

    def __init__(self, path):
        self.path = path
        self.shelf = shelve.open(path)
        self.tracked_classes = set()
        self.tracked_objects = {}

    def cache(self, f):
        filepath   = f.__globals__['__file__']
        name       = f.__qualname__
        try:
            class_name = f.__qualname__.rsplit(".", 2)[-2]
        except IndexError:
            class_name = None

        def wrapper(*args, **kwargs):
            key = CacheKey()
            key.append(filepath)
            key.append(name)
            key.append(str(len(args)))
            key.append(str(len(kwargs)))

            arguments = args
            object_state = None
            if class_name is not None:
                if self.is_tracked_class(filepath, class_name):
                    method_self = args[0]
                    arguments = args[1:]
                    self_signature = self.get_tracked_object_signature(method_self)
                    key.append(self_signature)
                    object_state = self.tracked_objects[id(method_self)]

            for argument in arguments:
                argument_id = get_signature(argument)
                key.append(argument_id)

            for keyword in kwargs:
                argument_id = get_signature(kwargs[keyword])
                key.append(keyword)
                key.append(argument_id)

            serialized_key = key.serialize()
            if serialized_key in self.shelf:
                result = self.shelf[serialized_key]
            else:
                if object_state is not None:
                    object_state.sync()
                result = f(*args, **kwargs)
                self.shelf[serialized_key] = result
            return result

        return wrapper

    def stateful(self, method):
        filepath   = method.__globals__['__file__']
        class_name = method.__qualname__.rsplit(".", 2)[-2]
        self.tracked_classes.add((filepath, class_name))

        def wrapper(*args, **kwargs):
            it = args[0]

            if id(it) not in self.tracked_objects:
                self.tracked_objects[id(it)] = ObjectState(it)
            state = self.tracked_objects[id(it)]

            state.append(method, args[1:], kwargs)

        return wrapper

    def sync(self, object):
        self.tracked_objects[id(object)].sync()

    def is_tracked_class(self, filepath, class_name):
        return (filepath, class_name) in self.tracked_classes

    def get_tracked_object_signature(self, it):
        if id(it) not in self.tracked_objects:
            self.tracked_objects[id(it)] = ObjectState(it)
        return self.tracked_objects[id(it)].serialize()

    def save(self):
        self.shelf.sync()

    def close(self):
        self.shelf.close()

    def __del__(self):
        self.close()


class ObjectState:

    def __init__(self, object):
        self.value = ""
        self.object = object
        self.calls = []

    def sync(self):
        for (method, args, kwargs) in self.calls:
            method(self.object, *args, **kwargs)
        self.calls = []

    def append(self, method, proper_args, kwargs):
        self.calls.append(
            (method, proper_args, kwargs)
        )

        self.value += method.__name__
        self.value += str(len(proper_args))
        self.value += str(len(kwargs))
        for argument in proper_args:
            self.value += get_signature(argument)
        for keyword in kwargs:
            self.value += keyword
            self.value += get_signature(kwargs[keyword])

    def serialize(self):
        return self.value

class CacheKey:

    def __init__(self):
        self.value = ""

    def append(self, signature):
        self.value += signature

    def serialize(self):
        return self.value


def get_signature(argument):
    try:
        argument_id = argument.cache_signature
    except AttributeError:
        argument_id = repr(argument)
    return argument_id
