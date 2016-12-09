from typing import Any, Sequence, Union

from bs4 import BeautifulSoup, Tag
from requests import Response
from requests.structures import CaseInsensitiveDict
from requests_toolbelt.multipart.decoder import BodyPart, MultipartDecoder

from rets.http.data import Object
from rets.errors import RetsApiError, RetsParseError

Response_ = Union[Response, BodyPart]


def parse_response(response: Response_) -> Any:
    content_type = response.headers['content-type']
    if 'text/xml' in content_type:
        return parse_xml(response)
    elif 'multipart/parallel' in content_type:
        return parse_multipart(response)
    elif 'text/html' in content_type:
        raise RetsParseError(response.content)
    return parse_body_part(response)


def parse_xml(response: Response_) -> Tag:
    root = BeautifulSoup(response.content, 'lxml-xml')

    rets_tag = root.find('RETS')
    if rets_tag is None:
        raise RetsParseError('missing RETS tag')

    reply_code = int(rets_tag.attrs['ReplyCode'])
    if reply_code:
        reply_text = rets_tag.attrs['ReplyText']
        raise RetsApiError(reply_code, reply_text, root.prettify())

    return rets_tag


def parse_body_part(response: Response_) -> Object:
    headers = response.headers
    return Object(
        mime_type=headers['content-type'],
        content_id=headers['content-id'],
        description=headers.get('content-description'),
        object_id=headers['object-id'],
        url=headers.get('location'),
        preferred='Preferred' in headers,
        data=response.content or None,
    )


def parse_multipart(response: Response_) -> Sequence[Any]:
    """
    RFC 2045 describes the format of an Internet message body containing a MIME message. The
    body contains one or more body parts, each preceded by a boundary delimiter line, and the
    last one followed by a closing boundary delimiter line. After its boundary delimiter line,
    each body part then consists of a header area, a blank line, and a body area.

    HTTP/1.1 200 OK
    Server: Apache/2.0.13
    Date: Fri, 22 OCT 2004 12:03:38 GMT
    Cache-Control: private
    RETS-Version: RETS/1.7.2
    MIME-Version: 1.0
    Content-Type: multipart/parallel; boundary="simple boundary"

    --simple boundary
    Content-Type: image/jpeg
    Content-ID: 123456
    Object-ID: 1

    <binary data>

    --simple boundary
    Content-Type: text/xml
    Content-ID: 123457
    Object-ID: 1

    <RETS ReplyCode="20403" ReplyText="There is no listing with that ListingID"/>

    --simple boundary--
    """
    multipart = MultipartDecoder.from_response(response, response.encoding)
    # We need to decode the headers because MultipartDecoder returns bytes keys and values,
    # while requests.Response.headers uses string keys and values.
    for part in multipart.parts:
        part.headers = _decode_headers(part.headers, response.encoding)
    return tuple(parse_response(part) for part in multipart.parts)


def _decode_headers(headers: CaseInsensitiveDict, encoding: str) -> CaseInsensitiveDict:
    return CaseInsensitiveDict({
        k.decode(encoding): v.decode(encoding)
        for k, v in headers.items()
    })
