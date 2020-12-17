from os import remove

from caching import Cache

remove("cache")

cache = Cache("cache")

state = False

@cache.cache
def f(x):
    global state
    state = True
    return x**2


class Sum:

    def __init__(self):
        self.value = 0

    @cache.stateful
    def add(self, term):
        global state
        state = True
        self.value += term

    @cache.cache
    def get_value(self):
        global state
        state = True
        return self.value


def test_function():
    assert f(1) == 1
    assert f(2) == 4


def test_caching():
    global state
    f(0)
    state = False
    f(0)
    assert state is False
    
def test_stateful():
    global state
    
    total = Sum()
    total.add(1)
    total.add(2)
    total.add(3)
    assert total.get_value() == 6
    
    state = False
    total = Sum()
    total.add(1)
    total.add(2)
    total.add(3)
    assert total.get_value() == 6
    assert state is False

    total.add(4)
    assert total.get_value() == 10