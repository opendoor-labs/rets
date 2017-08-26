import logging
from collections import OrderedDict
from datetime import datetime, time, timezone
from decimal import Decimal
from functools import partial
from typing import Any, Sequence

import udatetime

from rets.errors import RetsParseError

logger = logging.getLogger('rets')


class RecordDecoder:

    def __init__(self, table: Sequence[dict], include_tz: bool = False):
        self._metadata_map = {field['SystemName']: field for field in table}
        self._include_tz = include_tz

    def decode(self, rows: Sequence[dict]) -> Sequence[dict]:
        if not rows:
            return ()

        # Build dict of field to decoder functions, assuming that all rows have the same fields.
        decoders = self._build_decoders(tuple(rows[0].keys()))

        def decode_field(field: str, value: str) -> Any:
            if value == '':
                return None
            return decoders[field](value)

        return tuple(OrderedDict((field, decode_field(field, value)) for field, value in row.items())
                     for row in rows)

    def _build_decoders(self, fields: Sequence[str]) -> dict:
        decoders = {}
        for field in fields:
            try:
                field_metadata = self._metadata_map[field]
            except KeyError:
                logger.warning('field %s not found in table metadata', field)
                field_metadata = {'DataType': 'Character'}

            decoders[field] = _get_decoder(
                data_type=field_metadata['DataType'],
                interpretation=field_metadata.get('Interpretation', ''),
                include_tz=self._include_tz,
            )

        return decoders


def _get_decoder(data_type: str, interpretation: str, include_tz: bool = False):
    if interpretation == _LOOKUP_TYPE:
        return str
    elif interpretation in _LOOKUP_MULTI_TYPES:
        return lambda value: value.split(',')

    if data_type in _TIMEZONE_AWARE_DECODERS:
        return partial(_TIMEZONE_AWARE_DECODERS[data_type], include_tz=include_tz)

    try:
        return _DECODERS[data_type]
    except KeyError:
        raise RetsParseError('unknown data type %s' % data_type) from None


def _decode_datetime(value: str, include_tz: bool) -> datetime:
    decoded = udatetime.from_string(value)
    if not include_tz:
        return decoded.astimezone(timezone.utc).replace(tzinfo=None)
    return decoded


def _decode_time(value: str, include_tz: bool) -> time:
    decoded = _decode_datetime('1970-01-01T' + value, include_tz)
    return decoded.time().replace(tzinfo=decoded.tzinfo)


_LOOKUP_TYPE = 'Lookup'

_LOOKUP_MULTI_TYPES = frozenset(('LookupMulti', 'LookupBitstring', 'LookupBitmask'))

_TIMEZONE_AWARE_DECODERS = {
    'DateTime': _decode_datetime,
    'Time': _decode_time,
}

_DECODERS = {
    'Boolean': lambda value: value == '1',
    'Character': str,
    'Date': lambda value: datetime.strptime(value, '%Y-%m-%d'),
    'Tiny': int,
    'Small': int,
    'Int': int,
    'Long': int,
    'Decimal': Decimal,
}
