import mimetypes
from typing import Optional, Sequence
import cgi

from requests import Response
from requests.structures import CaseInsensitiveDict
from requests_toolbelt.multipart.decoder import MultipartDecoder

from rets.errors import RetsApiError, RetsResponseError
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
    content_type = response.headers.get('content-type')

    if content_type and 'multipart/parallel' in content_type:
        return _parse_multipart(response)

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

    content_id = headers.get('content-id')
    object_id = headers.get('object-id')
    preferred = 'preferred' in headers
    description = headers.get('content-description')
    location = headers.get('location')
    content_type = headers.get('content-type')
    mime_type = _parse_mime_type(content_type) if content_type else None

    # Check XML responses first, it may contain an error description.
    if mime_type == 'text/xml':
        try:
            parse_xml(part)
        except RetsApiError as e:
            if e.reply_code == 20403:  # No object found
                return None
            raise

    # All RETS responses _must_ have `Content-ID` and `Object-ID` headers.
    if not content_id or not object_id:
        raise RetsResponseError(part.content, part.headers)

    # Respond with `Location` header redirect.
    if location:
        return Object(
            mime_type=_guess_mime_type(location) or mime_type,
            content_id=content_id,
            description=description,
            object_id=object_id,
            url=location,
            preferred=preferred,
            data=None,
        )

    # Check the `Content-Type` header exists for object responses.
    if mime_type is None or mime_type == 'text/html':
        raise RetsResponseError(part.content, part.headers)

    return Object(
        mime_type=mime_type,
        content_id=content_id,
        description=description,
        object_id=object_id,
        url=None,
        preferred=preferred,
        data=part.content or None,
    )


def _guess_mime_type(location: str) -> Optional[str]:
    mime_type, _ = mimetypes.guess_type(location)
    return mime_type


def _parse_mime_type(content_type: str) -> Optional[str]:
    # Parse mime type from content-type header, e.g. 'image/jpeg;charset=US-ASCII' -> 'image/jpeg'
    mime_type, _ = cgi.parse_header(content_type)
    return mime_type or None


def _decode_headers(headers: CaseInsensitiveDict, encoding: str) -> CaseInsensitiveDict:
    return CaseInsensitiveDict({
        k.decode(encoding): v.decode(encoding)
        for k, v in headers.items()
    })
