import enum
import http.server
from typing import Tuple, Callable


class RequestDescriptor:
    def __init__(self, name: str, qd: dict[str, Callable[[str], any]], func: Callable[[...], Tuple[int, dict, str]]):
        self.name = name
        self.query_descriptor = qd
        self.func = func

    @property
    def qd(self):
        return self.query_descriptor


class RequestCollection:
    def __init__(self):
        self.getters: dict[str, RequestDescriptor] = {}

    def add_get(self, name: str, qd: dict[str, Callable[[str], any]], func: Callable[[...], Tuple[int, dict, str]]):
        self._check_handler_name(name)
        self.getters[name] = RequestDescriptor(name, qd, func)

    def _check_handler_name(self, name):
        check = next((item for item in self.getters.keys() if name.find(item) != 0), None)
        assert check is None, f'Can\'t add request {name}, already exists: {check}'

    def __getitem__(self, item):
        return self.getters[item]

    def keys_get(self):
        return self.getters.keys()

    def values_get(self):
        return self.getters.values()

    def items_get(self):
        return self.getters.items()


class HTTPHandler(http.server.BaseHTTPRequestHandler):
    request_collection = RequestCollection()

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

    def send_fast_response(self, code):
        self.send_response(code)
        self.end_headers()

    def do_GET(self):
        path, qd = self.parse_path()
        if path not in self.request_collection.keys_get():
            self.send_fast_response(http.HTTPStatus.NOT_FOUND)
            return

        rq = self.request_collection[path]
        for key, value in qd.items():
            qd[key] = rq.qd[key](value)
        code, headers, result = rq.func(**qd)
        self.send_response(code)
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(result.encode('utf-8'))

    def parse_path(self):
        tmp = self.path.split("?")
        path = tmp[0]
        path = path.split("#")[0]

        if len(tmp) <= 1:
            return path, {}

        qd = {}
        for q in tmp[1].split('&'):
            name, value = q.split('=')
            qd[name] = value
        return path, qd

    def add_get(self, name, descriptor: dict[str, Callable[[str], any]], func: Callable[[...], Tuple[int, dict, str]]):
        self.request_collection.add_get(name, descriptor, func)


class HTTPType(enum.Enum):
    GET = 0
    OTHER = 1


class HTTPRequestBuilder:
    handlers = RequestCollection()

    def add(self, tpe: HTTPType, name, qd: dict[str, Callable[[str], any]], func):
        if tpe == HTTPType.GET:
            self.handlers.add_get(name, qd, func)

    def getter(self, name: str, qd: dict[str, Callable[[str], any]]):
        def inner(func):
            self.add(HTTPType.GET, name, qd, func)

        return inner

    def build(self):
        return type('SomeHTTPHandler', (HTTPHandler,), HTTPHandler.__dict__ | {'request_collection': self.handlers})


if __name__ == "__main__":
    builder = HTTPRequestBuilder()


    @builder.getter(name="/ping", qd={'val': int})
    def ping(val=1, **kwargs):
        res = ''
        for i in range(val):
            res += 'pong'

        return 200, {}, res


    print(builder.handlers.getters)
    server = http.server.HTTPServer(('localhost', 8080), builder.build())
    server.serve_forever()
