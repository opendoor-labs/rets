from collections import OrderedDict
from datetime import datetime, time
from decimal import Decimal
from typing import Any, Set, Sequence

from rets.errors import RetsParseError

import udatetime


class Table:

    def __init__(self, resource_class, fields: Sequence[dict]):
        self.resource = resource_class.resource
        self.resource_class = resource_class
        self._fields = fields

        self._parsers = {
            field['SystemName']: _get_parser(field['DataType'], field['Interpretation'])
            for field in self._fields
        }

    @property
    def metadata(self) -> Sequence[dict]:
        return tuple(self._fields)

    @property
    def fields(self) -> Set[str]:
        return set(self._parsers)

    def parse(self, row: dict, include_tz: bool = False) -> dict:
        return OrderedDict(
            (field, self.parse_field(field, value, include_tz))
            for field, value in row.items()
        )

    def parse_field(self, field: str, value: str, include_tz: bool = False) -> Any:
        if value == '':
            return None
        return self._parsers[field](value, include_tz=include_tz)

    def __repr__(self) -> str:
        return '<Table: %s:%s>' % (self.resource.name, self.resource_class.name)


def _get_parser(data_type: str, interpretation: str):
    if interpretation == _LOOKUP_TYPE:
        return _parse_str
    elif interpretation in _LOOKUP_MULTI_TYPES:
        return _parse_multi

    try:
        return _DATA_TYPE_PARSERS[data_type]
    except KeyError:
        raise RetsParseError('unknown data type %s' % data_type) from None


def _parse_boolean(value: str, **kwargs) -> bool:
    return value == '1'


def _parse_str(value: str, **kwargs) -> str:
    return str(value)


def _parse_int(value: str, **kwargs) -> int:
    return int(value)


def _parse_decimal(value: str, **kwargs) -> Decimal:
    return Decimal(value)


def _parse_date(value: str, **kwargs) -> datetime:
    return datetime.strptime(value, '%Y-%m-%d')


def _parse_datetime(value: str, include_tz: bool, **kwargs) -> datetime:
    parsed_datetime = udatetime.from_string(value)
    if not include_tz:
        return parsed_datetime.replace(tzinfo=None) + parsed_datetime.utcoffset()
    return parsed_datetime


def _parse_time(value: str, include_tz: bool, **kwargs) -> time:
    parsed_datetime = _parse_datetime('1970-01-01T' + value, include_tz)
    return parsed_datetime.time().replace(tzinfo=parsed_datetime.tzinfo)


def _parse_multi(value: str, **kwargs) -> Sequence[str]:
    return str(value).split(',')


_LOOKUP_TYPE = 'Lookup'

_LOOKUP_MULTI_TYPES = frozenset(('LookupMulti', 'LookupBitstring', 'LookupBitmask'))

_DATA_TYPE_PARSERS = {
    'Boolean': _parse_boolean,
    'Character': _parse_str,
    'Date': _parse_date,
    'DateTime': _parse_datetime,
    'Time': _parse_time,
    'Tiny': _parse_int,
    'Small': _parse_int,
    'Int': _parse_int,
    'Long': _parse_int,
    'Decimal': _parse_decimal,
}
