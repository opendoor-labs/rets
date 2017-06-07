from collections import OrderedDict
from datetime import datetime
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

    def parse(self, row: dict) -> dict:
        return OrderedDict(
            (field, self.parse_field(field, value))
            for field, value in row.items()
        )

    def parse_field(self, field: str, value: str) -> Any:
        if value == '':
            return None
        return self._parsers[field](value)

    def __repr__(self) -> str:
        return '<Table: %s:%s>' % (self.resource.name, self.resource_class.name)


def _get_parser(data_type: str, interpretation: str):
    if interpretation == _LOOKUP_TYPE:
        return _LOOKUP_PARSER
    elif interpretation in _LOOKUP_MULTI_TYPES:
        return _LOOKUP_MULTI_PARSER

    try:
        return _DATA_TYPE_PARSERS[data_type]
    except KeyError:
        raise RetsParseError('unknown data type %s' % data_type) from None


_LOOKUP_TYPE = 'Lookup'
_LOOKUP_PARSER = str

_LOOKUP_MULTI_TYPES = frozenset(('LookupMulti', 'LookupBitstring', 'LookupBitmask'))
_LOOKUP_MULTI_PARSER = lambda value: str(value).split(',')

_DATA_TYPE_PARSERS = {
    'Boolean': lambda value: value == '1',
    'Character': str,
    'Date': lambda value: datetime.strptime(value, '%Y-%m-%d'),
    'DateTime': udatetime.from_string,
    'Tiny': int,
    'Small': int,
    'Int': int,
    'Long': int,
    'Decimal': Decimal,
}
