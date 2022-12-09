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
        self.getters: dict[str, RequestDescriptor] = {}
        self.posters: dict[str, RequestDescriptor] = {}

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
        if tpe == HTTPType.GET:
            return self.getters
        if tpe == HTTPType.POST:
            return self.posters
        raise Exception("Request handler not found: " + str(tpe))

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

    def do_GET(self):
        path, query = self.parse_path()
        if path not in self.request_collection.keys(HTTPType.GET):
            self.send_fast_response(http.HTTPStatus.NOT_FOUND)
            return

        rq = self.request_collection[HTTPType.GET][path]
        for key, value in query.items():
            query[key] = rq.qd[key](value)
        code, headers, result = rq.func(**query, infile=self.rfile)
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


class HTTPRequestBuilder:
    handlers = RequestCollection()

    def add(self, tpe: HTTPType, name, qd: dict[str, Callable[[str], any]], func):
        self.handlers.add(tpe, name, qd, func)

    def get(self, name: str, qd: dict[str, Callable[[str], any]]):
        def inner(func):
            self.add(HTTPType.GET, name, qd, func)

        return inner

    def post(self, name: str, qd: dict[str, Callable[[str], any]]):
        def inner(func):
            self.add(HTTPType.POST, name, qd, func)

        return inner

    def build(self):
        return type('SomeHTTPHandler', (HTTPHandler,), HTTPHandler.__dict__ | {'request_collection': self.handlers})


if __name__ == "__main__":
    builder = HTTPRequestBuilder()


    @builder.get(name="/ping", qd={'val': int})
    def ping(val=1, **kwargs):
        res = ''
        for i in range(val):
            res += 'pong'

        return 200, {}, res


    @builder.get(name="/pong", qd={'val': int})
    def pong(val=1, **kwargs):
        res = ''
        for i in range(val):
            res += 'ping'

        return 200, {}, res


    @builder.post(name="/remember", qd={})
    def remember(**kwargs):
        infile = kwargs['rfile']
        print(infile.read())


    # print(builder.handlers.getters)
    server = http.server.HTTPServer(('localhost', 8080), builder.build())
    server.serve_forever()
