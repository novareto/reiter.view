import pytest
from horseman.http import HTTPError
from reiter.view.meta import View
from reiter.view.composed import ComposedView


class FakeTemplate:

    def render(self, **namespace):
        pages = [p[0] for p in namespace['pages']]
        return (
            f'A composed page. It contains {namespace["innerpage"]!r}. '
            f'It has the following pages : {", ".join(pages)}.'
        )


class MyComposedView(ComposedView):

    template = FakeTemplate()

    def get_name(self):
        return self.request.query.get('page', 'default')


class PersonView(MyComposedView):
    pass


class ItemView(MyComposedView):
    pass


class TestComposedView:

    def teardown_method(self, test_method):
        PersonView.pages.clear()
        ItemView.pages.clear()

    def test_default_pages(self):
        assert PersonView.pages == {}
        assert ItemView.pages == {}
        assert PersonView.pages is not ItemView.pages

    def test_page_decorator(self, environ):

        @PersonView.pages.register(name='biography')
        class Biography(View):

            def render(self):
                return "This is my life"

        assert PersonView.pages == {'biography': Biography}
        assert ItemView.pages == {}

    def test_page_rendering_no_page(self, request_class, environ):
        # no registered page
        request = request_class(environ)
        composed_view = PersonView(request)
        with pytest.raises(HTTPError):
            composed_view()

    def test_page_rendering_not_default(self, request_class, environ):
        request = request_class(environ)
        request.query['page'] = ['biography']

        @PersonView.pages.register(name='biography')
        class Biography(View):

            def GET(self):
                return "This is my life"

        @PersonView.pages.register(name='CV')
        class CuriculumVitae(View):

            def GET(self):
                return "This is my CV"

        composed_view = PersonView(request)
        response = composed_view()
        assert response.body == (
            "A composed page. It contains 'This is my life'. "
            "It has the following pages : biography, CV."
        )
