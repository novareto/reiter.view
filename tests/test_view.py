import pytest
from horseman.response import reply, Response
from horseman.http import HTTPError
from reiter.view.meta import APIView


class FakeTemplate:

    def render(self, **namespace):
        keys = list(namespace.keys())
        return f"This is my template and the namespace has keys: {keys}."


class MyView(APIView):

    def GET(self):
        return 'This is my GET body'

    def POST(self):
        return 'And this is my POST body'

    def PUT(self):
        return reply(200, 'This is my PUT body')

    def OPTIONS(self):
        return {
            'Some': 'info'
        }


class TemplateView(MyView):
    template = FakeTemplate()


class TestView:

    def test_view_instanciation(self, request_class, environ):
        request = request_class(environ)
        view = MyView(request, key="value", foo="bar")
        assert view.request is request
        assert view.params == {
            'key': 'value',
            'foo': 'bar'
        }

    def test_view_resolve(self, request_class, environ):
        request = request_class(environ)
        response = MyView.resolve(request, key="value", foo="bar")
        assert response.body == 'This is my GET body'

    def test_view_wrong_method(self, request_class, environ):
        request = request_class({**environ, 'REQUEST_METHOD': 'DELETE'})
        with pytest.raises(HTTPError) as exc:
            MyView.resolve(request)
        assert exc.value.status == 405
        assert exc.value.body == (
            'Specified method is invalid for this resource')

    def test_view_no_template(self, request_class, environ):
        request = request_class(environ)
        view = MyView(request)
        response = view()
        assert isinstance(response, Response)
        assert response.body == 'This is my GET body'

        request = request_class({**environ, 'REQUEST_METHOD': 'POST'})
        view = MyView(request)
        response = view()
        assert isinstance(response, Response)
        assert response.body == 'And this is my POST body'

        request = request_class({**environ, 'REQUEST_METHOD': 'PUT'})
        view = MyView(request)
        response = view()
        assert isinstance(response, Response)
        assert response.body == 'This is my PUT body'

        request = request_class({**environ, 'REQUEST_METHOD': 'OPTIONS'})
        view = MyView(request)
        with pytest.raises(ValueError) as exc:
            view()
        assert str(exc.value) == (
            "Can't render. The returned value is : {'Some': 'info'}."
        )

    def test_view_raw(self, request_class, environ):
        request = request_class(environ)
        view = MyView(request)
        response = view(raw=True)
        assert isinstance(response, str)
        assert response == 'This is my GET body'

        request = request_class({**environ, 'REQUEST_METHOD': 'OPTIONS'})
        view = MyView(request)
        response = view(raw=True)
        assert response == {'Some': 'info'}

    def test_view_with_template(self, request_class, environ):
        request = request_class({**environ, 'REQUEST_METHOD': 'POST'})
        view = TemplateView(request)
        response = view()
        assert isinstance(response, Response)
        assert response.body == 'And this is my POST body'

        request = request_class({**environ, 'REQUEST_METHOD': 'OPTIONS'})
        view = TemplateView(request)
        response = view()
        assert isinstance(response, Response)
        assert response.body == (
            "This is my template and the namespace has keys: "
            "['request', 'view', 'Some']."
        )
