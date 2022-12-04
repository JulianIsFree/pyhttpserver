import enum


class HTTPRequestType(enum.Enum):
    GET = "GET"
    POST = "POST"
    HEAD = "HEAD"
    OTHER = "NOT_IMPLEMENTED"


def _handler_name(name: str,
                  request_type: HTTPRequestType) -> str:  # TODO remove this as dict problem within handler solved
    return f'{request_type.name}:{name}'
