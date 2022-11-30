import typing
from typing import Callable

from handlers import MyHTTPHandler


class ClassBuilder:
    def __init__(self, clazz):
        self.params = {}
        self.clazz = clazz

    def add(self, mapping: str, handler_method: Callable[..., tuple[int, typing.ByteString, dict]]) -> 'ClassBuilder':
        self.params[mapping] = handler_method
        return self

    def build(self, update: dict = None):
        if update is None:
            update = {}
        assert len(update.keys() & self.params.keys()) == 0, "Bad things, if params and rewritten __dict__ overlaps"
        t = type('SomeHandler', (self.clazz,), dict(self.clazz.__dict__) | update | self.params)
        return t


class HandlerBuilder(ClassBuilder):
    def __init__(self):
        super().__init__(MyHTTPHandler)

    def build(self, with_root: str = None):
        def constructor_with_root_path(self, request, client_address, server):
            self.__class__.__base__.__init__(self, request, client_address, server, directory=with_root)

        t = super().build(None if with_root is None else {"__init__": constructor_with_root_path})
        t.__dict__['handlers'].update(self.params)

        return t
