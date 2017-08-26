from typing import FrozenSet, Mapping, Sequence, Union

from rets.client.decoder import RecordDecoder
from rets.client.record import Record
from rets.client.utils import get_metadata_data
from rets.errors import RetsClientError
from rets.http import RetsHttpClient, SearchResult


class ResourceClass:

    def __init__(self, resource, metadata: dict, http_client: RetsHttpClient):
        self.resource = resource
        self._http = http_client
        self._metadata = metadata
        self._table = metadata.get('_table')
        self._fields = None

    @property
    def name(self) -> str:
        return self._metadata['ClassName']

    @property
    def has_key_index(self) -> bool:
        return self._metadata.get('HasKeyIndex') == '1'

    @property
    def metadata(self) -> dict:
        metadata = dict(self._metadata)
        if self._table:
            metadata['_table'] = self._table
        return metadata

    @property
    def table(self) -> Sequence[dict]:
        if self._table is None:
            self._table = tuple(get_metadata_data(self._http, 'table', resource=self.resource.name, class_=self.name))
        return self._table

    @property
    def fields(self) -> FrozenSet[str]:
        if self._fields is None:
            self._fields = frozenset(field['SystemName'] for field in self.table)
        return self._fields

    def search(self,
               query: Union[str, Mapping[str, str]],
               fields: Sequence[str] = None,
               parse: bool = True,
               include_tz: bool = False,
               **kwargs) -> SearchResult:
        query = self._validate_query(query)
        if fields:
            fields = self._validate_fields(fields)

        result = self._http.search(
            resource=self.resource.name,
            class_=self.name,
            query=query,
            select=fields,
            **kwargs,
        )

        if parse:
            decoder = RecordDecoder(self.table, include_tz)
            rows = decoder.decode(result.data)
        else:
            rows = result.data

        return SearchResult(
            count=result.count,
            max_rows=result.max_rows,
            data=tuple(Record(self, row) for row in rows),
        )

    def _validate_query(self, query: Union[str, Mapping[str, str]]) -> str:
        if isinstance(query, str):
            return query
        self._assert_fields(query)
        return ','.join('(%s=%s)' % (field, value) for field, value in query.items())

    def _validate_fields(self, fields: Sequence[str]) -> str:
        self._assert_fields(fields)
        return ','.join(fields)

    def _assert_fields(self, fields: Sequence[str]) -> None:
        permissible = self.fields
        invalid = tuple(f for f in fields if f not in permissible)
        if invalid:
            raise RetsClientError('invalid fields %s' % ','.join(invalid))

    def __repr__(self) -> str:
        return '<Class: %s:%s>' % (self.resource.name, self.name)
