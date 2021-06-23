import inspect
from typing import get_args
from typing import Callable, Generator, Optional, Tuple, Iterable
from horseman.meta import Overhead
from horseman.types import WSGICallable, HTTPMethod
from reiter.view.meta import View


Endpoint = Callable[[Overhead], WSGICallable]
METHODS = frozenset(get_args(HTTPMethod))


def routables(view, methods: Optional[Iterable[HTTPMethod]] = None) -> \
    Generator[Tuple[HTTPMethod, Endpoint], None, None]:

    if inspect.isfunction(view):
        if methods is None:
            methods = ['GET']
        for method in methods:
            if method not in METHODS:
                raise ValueError(
                    f"'{method}' is not a known HTTP method.")
            yield method, view
    else:
        assert inspect.isclass(view) and issubclass(view, View), \
            f'{view} needs to be a subclass of {View}'
        assert methods is None
        for method in METHODS:
            if getattr(view, method, None) is not None:
                yield method, view.resolve
