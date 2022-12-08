from typing import Tuple, Callable, TypeVar

T = TypeVar('T')


class QueryDescriptorNameException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class QueryDescriptor(Tuple[str, Callable[[str], T]]):
    def __init__(self, name, caster):
        self.check_name(name)
        super().__init__(name, caster)
        self.caster = caster
        self.name = name

    def __new__(cls, name, caster):
        super().__new__(name, caster)

    def cast(self, v: str) -> T:
        return super()[1](v)

    @classmethod
    def check_name(cls, name: str):
        if name[0] == "" or name is None:
            raise QueryDescriptorNameException("Name must not be empty or None")

        if name[0].isnumeric():
            raise QueryDescriptorNameException("Name can't start with digit")


class RequestDescriptor:
    def __init__(self, name: str, qd: QueryDescriptor):
        self.name = name
        self.query_descriptor = qd

    @property
    def qd(self):
        return self.query_descriptor


class RequestCollection:
    def __init__(self, handlers=None):
        if handlers is None:
            handlers = {}
        self.handlers: dict[str, RequestDescriptor] = handlers

    def add(self, name: str, qd: QueryDescriptor):
        self._check_handler_name(name)
        self.handlers[name] = RequestDescriptor(name, qd)

    def _check_handler_name(self, name):
        check = next((item for item in self.handlers.keys() if name.find(item) != 0), None)
        assert check is None, f'Can\'t add request {name}, already exists: {check}'

