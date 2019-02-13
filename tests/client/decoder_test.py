from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

import pytest

from rets.client.decoder import (
    RecordDecoder,
    _get_decoder,
    _decode_datetime,
    _decode_time,
    _decode_date,
)


@pytest.fixture
def decoder():
    return RecordDecoder(({
        'SystemName': 'mls_number',
        'DataType': 'Character',
    }, {
        'SystemName': 'mod_timestamp',
        'DataType': 'DateTime',
    }, {
        'SystemName': 'list_date',
        'DataType': 'Date',
    }, {
        'SystemName': 'list_price',
        'DataType': 'Int',
    }))


def test_decode_rows(decoder):
    rows = decoder.decode(({
        'mls_number': '1',
        'mod_timestamp': '2017-08-01T12:00:00',
        'list_date': '2017-08-01',
        'list_price': '150000',
    }, {
        'mls_number': '2',
        'mod_timestamp': '2017-08-02T12:00:00',
        'list_date': '2017-08-02',
        'list_price': '250000',
    }))

    assert rows == ({
        'mls_number': '1',
        'mod_timestamp': datetime(2017, 8, 1, 12),
        'list_date': datetime(2017, 8, 1),
        'list_price': 150000,
    }, {
        'mls_number': '2',
        'mod_timestamp': datetime(2017, 8, 2, 12),
        'list_date': datetime(2017, 8, 2),
        'list_price': 250000,
    })


def test_decode_rows_missing_field(decoder):
    rows = decoder.decode(({
        'new_field': 'value',
    },))

    assert rows == ({'new_field': 'value'},)


def test_get_decoder():
    parser = _get_decoder('Character', '')
    assert parser('test') == 'test'

    parser = _get_decoder('Boolean', '')
    assert parser('1') == True
    assert parser('0') == False

    parser = _get_decoder('Date', '')
    assert parser('2017-01-02') == datetime(2017, 1, 2)

    parser = _get_decoder('Tiny', '')
    assert parser('1') == 1

    parser = _get_decoder('Small', '')
    assert parser('1') == 1

    parser = _get_decoder('Int', '')
    assert parser('1') == 1

    parser = _get_decoder('Long', '')
    assert parser('1') == 1

    parser = _get_decoder('Decimal', '')
    assert parser('1.2345') == Decimal('1.2345')

    parser = _get_decoder('Character', 'Lookup')
    assert parser('test') == 'test'

    parser = _get_decoder('Character', 'LookupMulti')
    assert parser('a,b,c') == ['a', 'b', 'c']

    parser = _get_decoder('Number', '')
    assert parser('214') == 214


def test_decode_datetime():
    assert _decode_datetime('2017-01-02T03:04:05', True) == \
           datetime(2017, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(0)))
    # TODO: The standard specifies that the second fraction is limited to one
    # digit, however udatetime only permits 3 or 6 digits.
    assert _decode_datetime('2017-01-02T03:04:05.600', True) == \
           datetime(2017, 1, 2, 3, 4, 5, 600000, tzinfo=timezone(timedelta(0)))
    assert _decode_datetime('2017-01-02T03:04:05Z', True) == \
           datetime(2017, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(0)))
    assert _decode_datetime('2017-01-02T03:04:05+00:00', True) == \
           datetime(2017, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(0)))
    assert _decode_datetime('2017-01-02T03:04:05-00:00', True) == \
           datetime(2017, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(0)))
    assert _decode_datetime('2017-01-02T03:04:05+07:08', True) == \
           datetime(2017, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=7, minutes=8)))
    assert _decode_datetime('2017-01-02T03:04:05.600+07:08', True) == \
           datetime(2017, 1, 2, 3, 4, 5, 600000, tzinfo=timezone(timedelta(hours=7, minutes=8)))
    assert _decode_datetime('2017-01-02T03:04:05-07:08', True) == \
           datetime(2017, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=-7, minutes=-8)))
    assert _decode_datetime('2017-01-02T03:04:05', False) == \
           datetime(2017, 1, 2, 3, 4, 5)
    assert _decode_datetime('2017-01-02T03:04:05.600', False) == \
           datetime(2017, 1, 2, 3, 4, 5, 600000)
    assert _decode_datetime('2017-01-02T03:04:05Z', False) == datetime(2017, 1, 2, 3, 4, 5)
    assert _decode_datetime('2017-01-02T03:04:05+00:00', False) == datetime(2017, 1, 2, 3, 4, 5)
    assert _decode_datetime('2017-01-02T03:04:05-00:00', False) == datetime(2017, 1, 2, 3, 4, 5)
    assert _decode_datetime('2017-01-02T12:00:00+07:08', False) == datetime(2017, 1, 2, 4, 52)
    assert _decode_datetime('2017-01-02T12:00:00-07:08', False) == datetime(2017, 1, 2, 19, 8)
    assert _decode_datetime('2017-01-01 00:00:00', False) == datetime(2017, 1, 1, 0, 0)
    assert _decode_datetime('2017-01-01', False) == datetime(2017, 1, 1, 0, 0)


def test_decode_time():
    assert _decode_time('03:04:05', True) == time(3, 4, 5, tzinfo=timezone(timedelta(0)))
    # TODO: The standard specifies that the second fraction is limited to one
    # digit, however udatetime only permits 3 or 6 digits.
    assert _decode_time('03:04:05.600', True) == time(3, 4, 5, 600000, tzinfo=timezone(timedelta(0)))
    assert _decode_time('03:04:05Z', True) == time(3, 4, 5, tzinfo=timezone(timedelta(0)))
    assert _decode_time('03:04:05+00:00', True) == time(3, 4, 5, tzinfo=timezone(timedelta(0)))
    assert _decode_time('03:04:05-00:00', True) == time(3, 4, 5, tzinfo=timezone(timedelta(0)))
    assert _decode_time('03:04:05+07:08', True) == time(3, 4, 5, tzinfo=timezone(timedelta(hours=7, minutes=8)))
    assert _decode_time('03:04:05-07:08', True) == time(3, 4, 5, tzinfo=timezone(timedelta(hours=-7, minutes=-8)))
    assert _decode_time('03:04:05.600+07:08', True) == \
           time(3, 4, 5, 600000, tzinfo=timezone(timedelta(hours=7, minutes=8)))
    assert _decode_time('03:04:05', False) == time(3, 4, 5)
    assert _decode_time('03:04:05.600', False) == time(3, 4, 5, 600000)
    assert _decode_time('03:04:05Z', False) == time(3, 4, 5)
    assert _decode_time('03:04:05+00:00', False) == time(3, 4, 5)
    assert _decode_time('03:04:05-00:00', False) == time(3, 4, 5)
    assert _decode_time('12:00:00+07:08', False) == time(4, 52)
    assert _decode_time('12:00:00-07:08', False) == time(19, 8)


def test_decode_date():
    assert _decode_date('2017-01-02T00:00:00.000', False) == datetime(2017, 1, 2, 0, 0, 0)
    assert _decode_date('2017-01-02', False) == datetime(2017, 1, 2, 0, 0, 0)
