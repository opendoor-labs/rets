from unittest.mock import MagicMock, call

from rets.http.client import (
    RetsHttpClient
)


def test_rets_ua_authorization_false():
    send_auth = False

    client = RetsHttpClient(login_url='test.url',
                            username='user',
                            password='pass',
                            send_rets_ua_authorization=send_auth,
                            )
    client._session = MagicMock()
    client._http_request(url='test.url')

    assert client._send_rets_ua_authorization == send_auth

    assert client._session.post.called
    assert 'RETS-UA-Authorization' not in client._session.post.call_args_list[0][1]['headers']


def test_rets_ua_authorization_default():
    # by default, sends 'RETS-UA-Authorization'
    client = RetsHttpClient(login_url='test.url',
                            username='user',
                            password='pass',
                            )
    client._session = MagicMock()
    client._http_request(url='test.url')

    assert client._session.post.called
    assert 'RETS-UA-Authorization' in client._session.post.call_args_list[0][1]['headers']
