from typing import Optional, Dict
from horseman.http import HTTPError
from reiter.view.meta import APIView


class PageRegistry(Dict[str, APIView]):

    def __init__(self, items: Optional[Dict[str, APIView]] = None):
        if items is not None:
            if not all(isinstance(key, str) for key in items):
                raise TypeError('All keys must be strings.')
            super().__init__(items)

    def add(self, page: APIView, name: str):
        self[name] = page

    def register(self, name: str):
        """Page decorator
        """
        def register_page(page: APIView) -> APIView:
            self.add(page, name)
            return page
        return register_page

    def __setitem__(self, name: str, page: APIView):
        if not isinstance(name, str):
            raise TypeError(f'Key must be a string. Got {type(name)}.')
        if not issubclass(page, APIView):
            raise TypeError(
                f'Value must be a subclass of {APIView}. Got {type(page)}.'
            )
        return super().__setitem__(name, page)


class ComposedViewMeta(type):

    def __init__(cls, name, bases, attrs):
        type.__init__(cls, name, bases, attrs)
        cls.pages = PageRegistry()


class ComposedView(APIView, metaclass=ComposedViewMeta):

    def GET(self):
        # allowed method
        pass

    def POST(self):
        # allowed method
        pass

    def get_name(self):
        raise NotImplementedError('Implement in your own class.')

    def update(self):
        name = self.get_name()
        page = self.pages.get(name)
        if page is None:
            raise HTTPError(400)
        self.page = page(self.request, **self.params)
        self.page.update()

    def __call__(self, **kwargs):
        self.update()
        body = self.page(raw=True)
        pages = list(self.pages.items())
        return self.render({
            "innerpage": body,
            "pages": pages,
            "view": self,
        }, **kwargs)
