from typing import Callable, Generator, Tuple
from horseman.http import HTTPError
from horseman.prototyping import WSGICallable, HTTPMethod


Endpoint = Callable[[Overhead], WSGICallable]


class View:

    def __init__(self, request: Overhead):
        self.request = request
        self.method = request.environ['REQUEST_METHOD'].upper()

    def update(self):
        pass

    def __call__(self):
        if worker := getattr(self, self.method, None):
            self.update()
            return worker()
        raise HTTPError(405)

    @classmethod
    def resolve(cls, request: Overhead):
        inst = cls(request)
        return inst()


def routables(view, methods=None) -> \
    Generator[Tuple[HTTPMethod, Endpoint], None, None]:

    assert methods is None
    assert inspect.isclass(view) and issubclass(view, GrokView), \
        f'{view} needs to be a subclass of {GrokView}'

    for method in METHODS:
        if getattr(view, method, None) is not None:
            yield method, view.resolve
