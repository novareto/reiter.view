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

    def __init__(self, request: Overhead, **params):
        self.request = request
        self.params = params
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
        return Response.redirect(location, code=code)

    def render(self, result: Result, raw=False, layout=...):
        if isinstance(result, str):
            if raw:
                return result
            return Response.create(body=result)

        if isinstance(result, (dict, type(None))):
            if self.template is None:
                raise ValueError(
                    "{self} returned a namespace but does "
                    "not define a template")
            if result is None:
                ns = self.namespace()
            else:
                ns = self.namespace(**result)
            if raw:
                return self.request.app.ui.render(
                    self.template, layout=layout, **ns)
            return self.request.app.ui.response(
                self.template, layout=layout, **ns)

        if isinstance(result, tuple):
            if len(result) == 1:
                body = result[0]
                code = 200
                headers = None
            elif len(result) == 2:
                body, code = result
                headers = None
            elif len(result) == 3:
                body, code, headers = result
            if raw:
                return body
            return Response.create(body=body, code=code, headers=headers)

        if isinstance(result, Response):
            if raw:
                raise ValueError('The view returned a Response object.')
            return result

        raise ValueError("Can't interpret return")

    def __call__(self, raw=False, layout=...):
        if worker := getattr(self, self.method, None):
            self.update()
            return self.render(worker(), raw=raw, layout=layout)
        raise HTTPError(405)

    @classmethod
    def resolve(cls, request: Overhead, **params):
        inst = cls(request, **params)
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
