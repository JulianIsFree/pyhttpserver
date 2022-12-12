import enum
import http.server
from typing import Tuple, Callable


class HTTPType(enum.Enum):
    OTHER = 0
    POST = 1
    GET = 2


class RequestDescriptor:
    def __init__(self, tpe: HTTPType, name: str, qd: dict[str, Callable[[str], any]],
                 func: Callable[[...], Tuple[int, dict, str]]):
        self.name = name
        self.query_descriptor = qd
        self.func = func
        self.tpe = tpe

    @property
    def qd(self):
        return self.query_descriptor


class RequestCollection:
    def __init__(self):
        self.handlers: dict[HTTPType, dict[str, RequestDescriptor]] = {}

    def add(self, tpe: HTTPType, name: str, qd: dict[str, Callable[[str], any]],
            func: Callable[[...], Tuple[int, dict, str]]):
        self._check_handler_name(tpe, name)
        self._requests_by_type(tpe)[name] = RequestDescriptor(HTTPType.GET, name, qd, func)

    def _check_handler_name(self, tpe: HTTPType, name):
        check = next((item for item in self._requests_by_type(tpe).keys() if name.find(item) == 0), None)
        assert check is None, f'Can\'t add request {name}, already exists: {check}'

    def __getitem__(self, tpe: HTTPType):
        return self._requests_by_type(tpe)

    def _requests_by_type(self, tpe: HTTPType):
        if tpe not in self.handlers.keys():
            self.handlers[tpe] = {}
        return self.handlers[tpe]

    def keys(self, tpe: HTTPType):
        return self._requests_by_type(tpe).keys()

    def values(self, tpe: HTTPType):
        return self._requests_by_type(tpe).values()

    def items_get(self, tpe: HTTPType):
        return self._requests_by_type(tpe).items()


class HTTPHandler(http.server.BaseHTTPRequestHandler):
    request_collection = RequestCollection()

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

    def send_fast_response(self, code):
        self.send_response(code)
        self.end_headers()

    def proceed_default(self, tpe: HTTPType):
        path, query = self.parse_path()
        if path not in self.request_collection.keys(tpe):
            self.send_fast_response(http.HTTPStatus.NOT_FOUND)
            return

        request_collection = self.request_collection[tpe][path]
        for key, value in query.items():
            if key in request_collection.qd.keys():
                query[key] = request_collection.qd[key](value)
        code, headers, result = request_collection.func(**query, infile=self.rfile, headers=self.headers)
        self.send_response(code)
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(result.encode('utf-8'))

    def do_GET(self):
        self.proceed_default(HTTPType.GET)

    def do_POST(self):
        self.proceed_default(HTTPType.POST)

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


class HTTPRequestBuilder:
    handlers = RequestCollection()

    def add(self, tpe: HTTPType, name, qd: dict[str, Callable[[str], any]], func):
        self.handlers.add(tpe, name, qd, func)

    def get(self, name: str, **qd):
        def inner(func):
            self.add(HTTPType.GET, name, qd, func)

        return inner

    def post(self, name: str, **qd):
        def inner(func):
            self.add(HTTPType.POST, name, qd, func)

        return inner

    def build(self):
        return type('SomeHTTPHandler', (HTTPHandler,), HTTPHandler.__dict__ | {'request_collection': self.handlers})


if __name__ == "__main__":
    builder = HTTPRequestBuilder()


    @builder.get(name="/ping", val=int)
    def ping(val=1, **kwargs):
        res = ''
        for i in range(val):
            res += 'pong'

        return 200, {}, res


    @builder.get(name="/pong", val=int)
    def pong(val=1, **kwargs):
        res = ''
        for i in range(val):
            res += 'ping'

        return 200, {}, res


    @builder.post(name="/remember")
    def remember(**kwargs):
        infile = kwargs['infile']
        headers = kwargs['headers']
        len = int(headers['Content-Length'])
        print(infile.read(len).decode('utf-8'))
        return 200, {}, ""


    # print(builder.handlers.getters)
    server = http.server.HTTPServer(('localhost', 8080), builder.build())
    server.serve_forever()
