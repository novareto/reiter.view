import inspect
from functools import partial
from typing import get_args
from typing import Callable, Generator, Optional, Tuple, Iterable
from horseman.meta import Overhead
from horseman.types import WSGICallable, HTTPMethod
from reiter.view.meta import View


Endpoint = Callable[[Overhead], WSGICallable]
METHODS = frozenset(get_args(HTTPMethod))


def routables(view, methods: Optional[Iterable[HTTPMethod]] = None) -> \
    Generator[Tuple[HTTPMethod, Endpoint], None, None]:

    def instance_members(cls):
        if methods is not None:
            raise AttributeError(
                'Registration of a View does not accept methods.')
        members = inspect.getmembers(
            cls, predicate=(lambda x: inspect.isfunction(x)
                             and x.__name__ in METHODS))

        for name, func in members:
            endpoint = partial(cls.resolve)
            endpoint.__doc__ = func.__doc__
            yield endpoint, [name]

    if inspect.isfunction(view):
        if methods is None:
            methods = ['GET']
        unknown = set(methods) - METHODS
        if unknown:
            raise ValueError(
                f"Unknown HTTP method(s): {', '.join(unknown)}")
        yield view, methods
    else:
        assert inspect.isclass(view) and issubclass(view, View), \
            f'{view} needs to be a subclass of {View}'
        yield from instance_members(view)
