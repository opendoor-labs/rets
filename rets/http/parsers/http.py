from typing import Any, Sequence, Tuple, Union
from xml.etree.ElementTree import XML, Element

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


def parse_xml(response: Response_) -> Element:
    root = XML(response.content)

    reply_code, reply_text = parse_rets_status(root)

    if reply_code:
        raise RetsApiError(reply_code, reply_text, response.content)

    return root


def parse_rets_status(root: Element) -> Tuple[int, str]:
    """
    If RETS-STATUS exists, the client must use this instead
    of the status from the body-start-line
    """
    rets_status = root.find('RETS-STATUS')
    elem = rets_status if rets_status is not None else root
    return (int(elem.get('ReplyCode')), elem.get('ReplyText'))


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
    # while requests.Response.headers uses str keys and values.
    for part in multipart.parts:
        part.headers = _decode_headers(part.headers, response.encoding)

    def parse_multipart(parts):
        for part in parts:
            try:
                yield parse_response(part)
            except RetsApiError as e:
                if e.reply_code != 20403:  # No object found
                    raise

    return tuple(parse_multipart(multipart.parts))


def _decode_headers(headers: CaseInsensitiveDict, encoding: str) -> CaseInsensitiveDict:
    return CaseInsensitiveDict({
        k.decode(encoding): v.decode(encoding)
        for k, v in headers.items()
    })
