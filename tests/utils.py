from requests import Response
from requests.structures import CaseInsensitiveDict
from requests.utils import get_encoding_from_headers


def make_response(status_code: int = 200,
                  content: bytes = b'',
                  headers: dict = None,
                  reason: str = None,
                  encoding: str = None,
                  ) -> Response:
    response = Response()
    response.status_code = status_code
    response._content = content
    response._content_consumed = True
    response.headers = CaseInsensitiveDict(headers or {})
    response.encoding = encoding or get_encoding_from_headers(headers or {})
    response.reason = reason
    return response
