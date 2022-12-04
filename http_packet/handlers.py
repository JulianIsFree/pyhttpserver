from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from urllib.parse import urlparse

from http_packet.util import HTTPRequestType, _handler_name


class HTTPHandler(SimpleHTTPRequestHandler):
    handlers = {}  # todo: make way to differ request types, now it's merging type name and mapping name
    apache_mode: str = None

    def __init__(self, request, client_address, server, directory: str = None, apache_mode: str = None):
        if apache_mode is not None:
            self.apache_mode = apache_mode
        super().__init__(request, client_address, server, directory=directory)

    def do_CONNECT(self):
        if 'Host' not in self.headers.keys():
            self.send_response_code_and_end(HTTPStatus.BAD_REQUEST)
            return

        self.send_response_code_and_end(HTTPStatus.BAD_REQUEST)

    def do_GET(self):
        # TODO: logging here and there
        try:
            path, params = get_method_name_and_query(self.path)
        except QueryArgumentException:
            self.send_response_code_and_end(HTTPStatus.BAD_REQUEST, "bad query")
            return

        if self.apache_mode is not None and path.startswith(self.apache_mode):
            self.path = path[path.find(self.apache_mode) + len(self.apache_mode)::]
            super().do_GET()
            return

        path = _handler_name(path, HTTPRequestType.GET)
        if path in self.handlers.keys():
            code, res, headers = self.handlers[path](**params)
            self.send_response(code)
            for header, value in headers.items():
                self.send_header(header, value)
            self.end_headers()
            self.wfile.write(res)
        else:
            self.send_response_code_and_end(HTTPStatus.NOT_FOUND)

    def do_POST(self):
        self.send_response_code_and_end(HTTPStatus.NOT_IMPLEMENTED)

    def do_HEAD(self):
        self.send_response_code_and_end(HTTPStatus.NOT_IMPLEMENTED)

    def send_response_code_and_end(self, code, msg=None):
        self.send_response(code, msg)
        self.end_headers()


def get_method_name_and_query(path: str) -> tuple[str, dict[str, str]]:
    parse_result = urlparse(path)
    query = parse_result.query if len(parse_result.query) > 0 else None
    path = parse_result.path

    query_dict = {}
    if query is not None:
        for p in query.split('&'):
            key, word = p.split('=')
            if key[0].isnumeric():
                raise QueryArgumentException(f'Query attribute name can\'t start with number: {key}')
            query_dict[key] = word

    return path, query_dict


class QueryArgumentException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
