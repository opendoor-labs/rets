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
            field['SystemName']: get_parser(field['DataType'])
            for field in self._fields
        }

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


def get_parser(data_type: str):
    try:
        return _PARSER_MAPPING[data_type]
    except KeyError:
        raise RetsParseError('unknown data type %s' % data_type) from None


_PARSER_MAPPING = {
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
