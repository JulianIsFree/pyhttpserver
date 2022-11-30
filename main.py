import http.server

from builders import HandlerBuilder


if __name__ == "__main__":
    hb = HandlerBuilder()\
        .add("/ping", lambda **kwargs: (200, "pong".encode("utf-8"), {}))
    handler = hb.build(with_root="C:/", apache_mode="/browse")

    server = http.server.HTTPServer(('localhost', 8080), RequestHandlerClass=handler)
    server.serve_forever()
