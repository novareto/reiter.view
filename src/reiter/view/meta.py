from abc import ABC, abstractmethod
from typing import Callable, Union, Dict, Any
from horseman.http import HTTPError
from horseman.meta import Overhead
from horseman.response import Response
from horseman.types import WSGICallable, HTTPMethod


Endpoint = Callable[[Overhead], WSGICallable]
Result = Union[str, Dict, Response, None]


class View:

    @classmethod
    def resolve(cls, request: Overhead, **params):
        inst = cls(request, **params)
        return inst()

    def __init__(self, request: Overhead, **params):
        self.request = request
        self.params = params

    def update(self):
        pass

    def redirect(self, location, code=302):
        return Response.redirect(location, code=code)

    def __call__(self, **kwargs):
        raise NotImplementedError('Override in your own subclass.')


class APIView(View):
    """View using the HTTP Method to find
    """
    template = None

    def namespace(self, **extra):
        return {
            'request': self.request,
            'view': self,
            **extra
        }

    def render(self, result: Any, **kwargs):
        if isinstance(result, Response):
            return result

        raw = kwargs.get('raw', False)
        if isinstance(result, str) and not raw:
            return Response.create(200, body=result)

        if isinstance(result, (dict, type(None))):
            if self.template is not None:
                if result is None:
                    ns = self.namespace()
                else:
                    ns = self.namespace(**result)
                result = self.template.render(**ns)
                if not raw:
                    return Response.create(200, body=result)

        if raw:
            return result
        raise ValueError(
            f"Can't render. The returned value is : {result!r}."
        )

    def __call__(self, **kwargs):
        method: HTTPMethod = self.request.environ['REQUEST_METHOD'].upper()
        if worker := getattr(self, method, None):
            self.update()
            return self.render(worker(), **kwargs)
        raise HTTPError(405)
