import http.server

from builders import HandlerBuilder


if __name__ == "__main__":
    hb = HandlerBuilder()\
        .add("/ping", lambda **kwargs: (200, "pong".encode("utf-8"), {}))
    server = http.server.HTTPServer(('localhost', 8080), RequestHandlerClass=hb.build("C:/"))
    server.serve_forever()
