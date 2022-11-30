from typing import Callable, ByteString

from handlers import HTTPHandler


class ClassBuilder:
    def __init__(self, clazz, allow_overlap_mapping=False):
        self.methods = {}
        self.clazz = clazz
        self.allow_overlap_mapping = allow_overlap_mapping

    def add(self, mapping: str, handler_method: Callable[..., tuple[int, ByteString, dict]]) -> 'ClassBuilder':
        if (not self.allow_overlap_mapping) and mapping in self.methods.keys():
            raise ClassBuilderOverlapException(f'Name {mapping} already added')
        self.methods[mapping] = handler_method
        return self

    def build(self, update: dict = None):
        if update is None:
            update = {}
        assert len(update.keys() & self.methods.keys()) == 0, "Bad things, if params and rewritten __dict__ overlaps"
        t = type('SomeHandler', (self.clazz,), dict(self.clazz.__dict__) | update | self.methods)
        return t


class HandlerBuilder(ClassBuilder):
    def __init__(self, http_handler_subclass=HTTPHandler, allow_overlap_mapping=False):
        assert issubclass(http_handler_subclass, HTTPHandler)
        super().__init__(http_handler_subclass, allow_overlap_mapping)

    def build(self, with_root: str = None, apache_mode: str = None):
        def constructor_with_root_path(self, request, client_address, server):
            self.__class__.__base__.__init__(self, request, client_address, server, directory=with_root)

        t = super().build(None if with_root is None else {"__init__": constructor_with_root_path, 'apache_mode': apache_mode})
        t.__dict__['handlers'].update(self.methods)
        return t


class ClassBuilderOverlapException(Exception):
    def __init__(self, msg):
        super(ClassBuilderOverlapException, self).__init__(msg)

