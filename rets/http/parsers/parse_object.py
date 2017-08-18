import mimetypes
from typing import Optional, Sequence

from requests import Response
from requests.structures import CaseInsensitiveDict
from requests.utils import cgi
from requests_toolbelt.multipart.decoder import MultipartDecoder

from rets.errors import RetsApiError, RetsParseError
from rets.http.data import Object
from rets.http.parsers.parse import DEFAULT_ENCODING, ResponseLike, parse_xml


def parse_object(response: Response) -> Sequence[Object]:
    """
    Parse the response from a GetObject transaction. If there are multiple
    objects to be returned then the response should be a multipart response.
    The headers of the response (or each part in the multipart response)
    contains the metadata for the object, including the location if requested.
    The body of the response should contain the binary content of the object,
    an XML document specifying a transaction status code, or left empty.
    """
    content_type = response.headers['content-type']

    if 'multipart/parallel' in content_type:
        return _parse_multipart(response)
    else:
        object_ = _parse_body_part(response)
        return (object_,) if object_ is not None else ()


def _parse_multipart(response: ResponseLike) -> Sequence[Object]:
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
    encoding = response.encoding or DEFAULT_ENCODING
    multipart = MultipartDecoder.from_response(response, encoding)
    # We need to decode the headers because MultipartDecoder returns bytes keys and values,
    # while requests.Response.headers uses str keys and values.
    for part in multipart.parts:
        part.headers = _decode_headers(part.headers, encoding)

    objects = (_parse_body_part(part) for part in multipart.parts)
    return tuple(object_ for object_ in objects if object_ is not None)


def _parse_body_part(part: ResponseLike) -> Optional[Object]:
    headers = part.headers
    content_type = headers['content-type']

    if 'text/xml' in content_type:
        try:
            parse_xml(part)
        except RetsApiError as e:
            if e.reply_code == 20403:  # No object found
                return None
            raise
    elif 'text/html' in content_type:
        raise RetsParseError(part.content)

    location = headers.get('location')
    if location:
        mime_type, _ = mimetypes.guess_type(location)
        data = None
    else:
        # Parse mime type from content-type header, e.g.
        # 'image/jpeg;charset=US-ASCII' -> 'image/jpeg'
        mime_type, _ = cgi.parse_header(headers['content-type'])
        data = part.content or None

    return Object(
        mime_type=mime_type,
        content_id=headers['content-id'],
        description=headers.get('content-description'),
        object_id=headers['object-id'],
        url=location,
        preferred='Preferred' in headers,
        data=data,
    )


def _decode_headers(headers: CaseInsensitiveDict, encoding: str) -> CaseInsensitiveDict:
    return CaseInsensitiveDict({
        k.decode(encoding): v.decode(encoding)
        for k, v in headers.items()
    })
