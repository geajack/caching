from os import remove

from caching import Cache, auto, state_modifying, nonlazy

try:
    remove("cache")
except FileNotFoundError:
    pass

cache = Cache("cache")

state = False

@cache.cached
def f(x):
    global state
    state = True
    return x**2
@auto
class Sum:

    global_state = 0

    def __init__(self, value=0):
        self.value = value

    @state_modifying
    def add(self, term):
        self.value += term

    @cache.cached
    def get_value(self):
        Sum.global_state += 1
        return self.value

square_state = False
@cache.cached
def square(summer):
    global square_state
    square_state = True
    return summer.get_value()**2

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

def test_auto_argument():
    global square_state

    total = Sum()
    total.add(2)
    assert square(total) == 4

    square_state = False
    assert square(total) == 4
    assert square_state is False

    state = False