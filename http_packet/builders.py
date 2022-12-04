from typing import Callable, ByteString

from handlers import HTTPHandler
from http_packet.util import HTTPRequestType, _handler_name


class ClassBuilder:
    def __init__(self, clazz, allow_overlap_mapping=False):
        self.methods = {}
        self.clazz = clazz
        self.allow_overlap_mapping = allow_overlap_mapping

    def _add(self, mapping: str, handler: Callable) -> 'ClassBuilder':
        if (not self.allow_overlap_mapping) and mapping in self.methods.keys():
            raise ClassBuilderOverlapException(f'Name {mapping} already added')
        self.methods[mapping] = handler
        return self

    def with_constructor(self, method: Callable) -> 'ClassBuilder':
        return self._add("__init__", method)

    def build(self):
        t = type('SomeClass', (self.clazz,), dict(self.clazz.__dict__) | self.methods)
        return t


class HandlerBuilder(ClassBuilder):
    def __init__(self, http_handler_subclass=HTTPHandler, allow_overlap_mapping=False):
        assert issubclass(http_handler_subclass, HTTPHandler)
        super().__init__(http_handler_subclass, allow_overlap_mapping)

    def _add(self, mapping: str, handler_method: Callable[..., tuple[int, ByteString, dict]]) -> 'ClassBuilder':
        return super()._add(mapping, handler_method)

    def build(self, with_root: str = None, apache_mode: str = None):
        def constructor_with_root_path(self, request, client_address, server):
            self.__class__.__base__.__init__(self, request, client_address, server, directory=with_root,
                                             apache_mode=apache_mode)

        super().with_constructor(constructor_with_root_path)
        t = super().build()
        t.__dict__['handlers'].update(self.methods)
        return t

    def request(self, name, request_type: HTTPRequestType):
        def with_name(handler_method: Callable[..., tuple[int, ByteString, dict]]):
            self._add(_handler_name(name, request_type), handler_method)

        return with_name


class ClassBuilderOverlapException(Exception):
    def __init__(self, msg):
        super(ClassBuilderOverlapException, self).__init__(msg)
