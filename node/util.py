

def typename(x):
    return type(x).__name__


def assert_type(x, expected):
    assert isinstance(x, expected), "expected {}, got {}".format(expected.__name__, typename(x))