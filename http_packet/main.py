import http.server

from builders import HandlerBuilder
from http_packet.util import HTTPRequestType

if __name__ == "__main__":
    hb = HandlerBuilder()


    @hb.request(name="/ping", request_type=HTTPRequestType.GET)
    def ping():
        return 200, "pong".encode("utf-8"), {}


    handler = hb.build(apache_mode='/browse')

    server = http.server.HTTPServer(('localhost', 8080), RequestHandlerClass=handler)
    server.serve_forever()
