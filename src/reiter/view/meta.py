import inspect
from typing import Callable, Generator, Tuple, Union, Dict
from horseman.definitions import METHODS
from horseman.http import HTTPError
from horseman.meta import Overhead
from horseman.response import Response
from horseman.prototyping import WSGICallable, HTTPMethod


Endpoint = Callable[[Overhead], WSGICallable]
Result = Union[str, Dict, Tuple, Response]


class View:

    template = None

    def __init__(self, request: Overhead):
        self.request = request
        self.method = request.environ['REQUEST_METHOD'].upper()

    def update(self):
        pass

    def namespace(self, **extra):
        return {
            'request': self.request,
            'view': self,
            **extra
        }

    def redirect(self, location, code=302):
        return Response.create(code=code, headers={"Location": location})

    def render(self, result: Result):
        if isinstance(result, Response):
            return result
        if isinstance(result, str):
            return Response.create(body=result)
        if isinstance(result, tuple):
            if len(result) == 1:
                return Response.create(body=result[0])
            if len(result) == 2:
                body, code = result
                return Response.create(body=body, code=code)
            if len(result) == 3:
                body, code, headers = result
                return Response.create(body=body, code=code, headers=headers)
            raise ValueError("Can't interpret return")
        if isinstance(result, dict):
            if self.template is None:
                raise ValueError(
                    "{self} returned a namespace but does "
                    "not define a template")
            ns = self.namespace(**result)
            return self.request.app.ui.response(self.template, **ns)
        return self

    def __call__(self):
        if worker := getattr(self, self.method, None):
            self.update()
            return self.render(worker())
        raise HTTPError(405)

    @classmethod
    def resolve(cls, request: Overhead):
        inst = cls(request)
        return inst()


def routables(view, methods=None) -> \
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
