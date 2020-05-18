from fuzzywuzzy import process


class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()

class staticproperty(property):
    def __get__(self, cls, owner):
        return staticmethod(self.fget).__get__(None, owner)()


def typename(x):
    return type(x).__name__


def assert_type(x, expected):
    assert isinstance(x, expected), "expected {}, got {}".format(expected.__name__, typename(x))


def attribute_error(name, k, keys):
    keys = list(keys)
    nearest, score = process.extractOne(k, keys)
    suggest = "" if score < 50 else "did you mean '{}'?".format(nearest)
    return AttributeError("{} has no attribute '{}', {}\noptions: {}"
        .format(name, k, suggest, keys))


class Namespace:
    def __init__(self, name, d):
        self._name = name 
        self._values = d

    def __str__(self):
        attrs = ["{}:{}".format(k, v) for k, v in self._values.items()]
        return "{}<{}>".format(self._name, ', '.join(attrs))

    def __repr__(self):
        return self.__str__()

    def __getattr__(self, attr):
        if attr not in self._values:
            raise attribute_error(self._name, attr, self.keys())

        value = self._values.get(attr)           
        return value

    def keys(self):
        return self._values.keys()
       
def namespace(_name, **d):
    return Namespace(_name, d)