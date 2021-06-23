import wrapt
from typing import Callable, Union, Dict
from horseman.http import HTTPError
from horseman.meta import Overhead
from horseman.response import Response
from horseman.types import WSGICallable, HTTPMethod


Endpoint = Callable[[Overhead], WSGICallable]
Result = Union[str, Dict, Response, None]


@wrapt.decorator
def response_wrapper(wrapped, instance, args, kwargs):
    raw = kwargs.get('raw', False)
    result: Result = wrapped(*args, **kwargs)
    if raw or isinstance(result, Response):
        return result

    if isinstance(result, str):
        return Response.create(body=result)

    raise ValueError("Can't interpret return")


class View:

    template = None

    @classmethod
    def resolve(cls, request: Overhead, **params):
        inst = cls(request, **params)
        return inst()

    def __init__(self, request: Overhead, **params):
        self.request = request
        self.params = params
        self.method: HTTPMethod = request.environ['REQUEST_METHOD'].upper()

    def redirect(self, location, code=302):
        return Response.redirect(location, code=code)

    def update(self):
        pass

    def namespace(self, **extra):
        return {
            'request': self.request,
            'view': self,
            **extra
        }

    @response_wrapper
    def render(self, result: Result, **kwargs):
        if self.template is None or \
            not isinstance(result, (dict, type(None))):
               return result
        if result is None:
            ns = self.namespace()
        else:
            ns = self.namespace(**result)
        return self.template.render(**ns)

    def __call__(self, **kwargs):
        if worker := getattr(self, self.method, None):
            self.update()
            return self.render(worker(), **kwargs)
        raise HTTPError(405)
