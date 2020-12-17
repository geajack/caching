from os import remove

from caching import Cache

cache = Cache("cache")

state = False

@cache.cache
def f(x):
    global state
    state = True
    return x**2


def test_function():
    assert f(1) == 1
    assert f(2) == 4


def test_caching():
    global state
    f(0)
    state = False
    f(0)
    assert state is False


def test_delete_cache():
    f(0)
    cache.save()
    remove("cache")
    state = False
    f(0)
    assert state is True
    