from rets import Object
from rets.http.parsers import parse_object
from tests.utils import make_response


def test_parse_object_single_location_true():
    headers = {
        'Content-Type': 'image/jpeg;charset=US-ASCII',
        'Content-ID': '20170817170218718581000000',
        'Object-ID': '1',
        'Location': 'http://cdn.rets.com/1.jpg',
        'Content-Description': 'anthem',
        'Preferred': '1',
    }
    body = b''
    response = make_response(200, body, headers)

    assert parse_object(response, False) == (
        Object(
            mime_type='image/jpeg',
            content_id='20170817170218718581000000',
            description='anthem',
            object_id='1',
            url='http://cdn.rets.com/1.jpg',
            preferred=True,
            data=None,
        ),
    )


def test_parse_object_single_location_false():
    headers = {
        'Content-Type': 'image/jpeg;charset=US-ASCII',
        'Content-ID': '20170817170218718581000000',
        'Object-ID': '1',
        'Content-Description': 'anthem',
        'Preferred': '1',
    }
    body = b'binary content'
    response = make_response(200, body, headers)

    assert parse_object(response, False) == (
        Object(
            mime_type='image/jpeg',
            content_id='20170817170218718581000000',
            description='anthem',
            object_id='1',
            url=None,
            preferred=True,
            data=b'binary content',
        ),
    )


def test_parse_object_not_found():
    headers = {
        'Content-Type': 'text/xml;charset=US-ASCII',
        'Content-ID': '201708171702187185810000009999',
        'Object-ID': '1',
        'Location': '',
    }
    body = b'<RETS ReplyCode="20403" ReplyText="No such object available for this resource"/>'
    response = make_response(200, body, headers)

    assert parse_object(response, False) == ()


def test_parse_object_multi_location_true():
    headers = {
        'Content-Type': 'multipart/parallel;boundary="FLEX1t7l9O45tdFUw2e92ASD3qKPxB0lf0Wo7atUz9qlAFoQdBGpDr";'
                        'charset=US-ASCII',
    }
    body = (
        b'\r\n--FLEX1t7l9O45tdFUw2e92ASD3qKPxB0lf0Wo7atUz9qlAFoQdBGpDr'
        b'\r\nContent-Type: image/jpeg'
        b'\r\nContent-ID: 20170817170218718581000000'
        b'\r\nObject-ID: 1'
        b'\r\nLocation: http://cdn.rets.com/1.jpg'
        b'\r\nContent-Description: anthem'
        b'\r\nPreferred: 1'
        b'\r\n\r\n'
        b'\r\n--FLEX1t7l9O45tdFUw2e92ASD3qKPxB0lf0Wo7atUz9qlAFoQdBGpDr'
        b'\r\nContent-Type: image/jpeg'
        b'\r\nContent-ID: 20170817170218718581000000'
        b'\r\nObject-ID: 2'
        b'\r\nLocation: http://cdn.rets.com/2.jpg'
        b'\r\nContent-Description: anthem2'
        b'\r\n\r\n'
        b'\r\n--FLEX1t7l9O45tdFUw2e92ASD3qKPxB0lf0Wo7atUz9qlAFoQdBGpDr--'
        b'\r\n'
    )
    response = make_response(200, body, headers)

    assert parse_object(response, False) == (
        Object(
            mime_type='image/jpeg',
            content_id='20170817170218718581000000',
            description='anthem',
            object_id='1',
            url='http://cdn.rets.com/1.jpg',
            preferred=True,
            data=None,
        ),
        Object(
            mime_type='image/jpeg',
            content_id='20170817170218718581000000',
            description='anthem2',
            object_id='2',
            url='http://cdn.rets.com/2.jpg',
            preferred=False,
            data=None,
        ),
    )


def test_parse_object_multi_location_false():
    headers = {
        'Content-Type': 'multipart/parallel;boundary="FLEX1t7l9O45tdFUw2e92ASD3qKPxB0lf0Wo7atUz9qlAFoQdBGpDr";'
                        'charset=US-ASCII',
    }
    body = (
        b'\r\n--FLEX1t7l9O45tdFUw2e92ASD3qKPxB0lf0Wo7atUz9qlAFoQdBGpDr'
        b'\r\nContent-Type: image/jpeg'
        b'\r\nContent-ID: 20170817170218718581000000'
        b'\r\nObject-ID: 1'
        b'\r\nContent-Description: anthem'
        b'\r\nPreferred: 1'
        b'\r\n'
        b'\r\nbinary content 1'
        b'\r\n--FLEX1t7l9O45tdFUw2e92ASD3qKPxB0lf0Wo7atUz9qlAFoQdBGpDr'
        b'\r\nContent-Type: image/jpeg'
        b'\r\nContent-ID: 20170817170218718581000000'
        b'\r\nObject-ID: 2'
        b'\r\nContent-Description: anthem2'
        b'\r\n'
        b'\r\nbinary content 2'
        b'\r\n--FLEX1t7l9O45tdFUw2e92ASD3qKPxB0lf0Wo7atUz9qlAFoQdBGpDr--'
        b'\r\n'
    )
    response = make_response(200, body, headers)

    assert parse_object(response, False) == (
        Object(
            mime_type='image/jpeg',
            content_id='20170817170218718581000000',
            description='anthem',
            object_id='1',
            url=None,
            preferred=True,
            data=b'binary content 1',
        ),
        Object(
            mime_type='image/jpeg',
            content_id='20170817170218718581000000',
            description='anthem2',
            object_id='2',
            url=None,
            preferred=False,
            data=b'binary content 2',
        ),
    )


def test_parse_object_no_encoding():
    # Note: there is no charset in the content-type
    headers = {
        'Content-Type': 'multipart/parallel;boundary="FLEX1t7l9O45tdFUw2e92ASD3qKPxB0lf0Wo7atUz9qlAFoQdBGpDr"'
    }
    body = (
        b'\r\n--FLEX1t7l9O45tdFUw2e92ASD3qKPxB0lf0Wo7atUz9qlAFoQdBGpDr'
        b'\r\nContent-Type: image/jpeg'
        b'\r\nContent-ID: 20170817170218718581000000'
        b'\r\nObject-ID: 1'
        b'\r\nLocation: http://cdn.rets.com/1.jpg'
        b'\r\nContent-Description: anthem'
        b'\r\nPreferred: 1'
        b'\r\n\r\n'
        b'\r\n--FLEX1t7l9O45tdFUw2e92ASD3qKPxB0lf0Wo7atUz9qlAFoQdBGpDr--'
        b'\r\n'
    )
    response = make_response(200, body, headers)

    assert parse_object(response, False) == (
        Object(
            mime_type='image/jpeg',
            content_id='20170817170218718581000000',
            description='anthem',
            object_id='1',
            url='http://cdn.rets.com/1.jpg',
            preferred=True,
            data=None,
        ),
    )


def test_parse_object_location_true_content_type_xml():
    headers = {
        'Content-Type': 'multipart/parallel; boundary=2ce97979.83bf.368b.86c2.cc9295f41e3d',
    }
    body = (
        b'\r\n--2ce97979.83bf.368b.86c2.cc9295f41e3d'
        b'\r\nContent-ID: 8240151'
        b'\r\nObject-ID: 1'
        b'\r\nLocation: http://cdn.rets.com/1.jpg'
        b'\r\nContent-Description: Welcome Home!'
        b'\r\nContent-Type: text/xml'
        b'\r\n'
        b'\r\n<RETS ReplyCode="0" ReplyText="SUCCESS" >\r\n</RETS>\r\n'
        b'\r\n--2ce97979.83bf.368b.86c2.cc9295f41e3d--'
        b'\r\n'
    )
    response = make_response(200, body, headers)

    assert parse_object(response, False) == (
        Object(
            mime_type='image/jpeg',
            content_id='8240151',
            description='Welcome Home!',
            object_id='1',
            url='http://cdn.rets.com/1.jpg',
            preferred=False,
            data=None,
        ),
    )
