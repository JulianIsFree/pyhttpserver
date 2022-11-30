import http.server
from urllib.parse import urlparse


class MyHTTPHandler(http.server.SimpleHTTPRequestHandler):
    handlers = {}

    def __init__(self, request, client_address, server, directory=None):
        super().__init__(request, client_address, server, directory=directory)

    def do_GET(self):
        path, params = translate_path_to_call(self.path)
        if path.startswith("/get"):
            self.path = path[path.find('/get') + 4::]
            super().do_GET()
        elif path in self.handlers.keys():
            code, res, headers = self.handlers[path](**params)
            self.send_response(code)
            for header, value in headers.items():
                self.send_header(header, value)
            self.end_headers()
            self.wfile.write(res)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        self.send_response(403)
        self.end_headers()

    def do_HEAD(self):
        self.send_response(403)
        self.end_headers()


def translate_path_to_call(path: str) -> tuple[str, dict[str, str]]:
    parse_result = urlparse(path)
    query = parse_result.query if len(parse_result.query) > 0 else None
    path = parse_result.path

    query_dict = {}
    if query is not None:
        for p in query.split('&'):
            key, word = p.split('=')
            query_dict[key] = word

    return path, query_dict
