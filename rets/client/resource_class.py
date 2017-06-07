from typing import Mapping, Sequence, Union, Optional

from rets.client.table import Table
from rets.client.record import Record
from rets.errors import RetsClientError
from rets.http import RetsHttpClient, SearchResult


class ResourceClass:

    def __init__(self, resource, metadata: dict, http_client: RetsHttpClient):
        self.resource = resource
        self._http = http_client
        self._metadata = metadata
        self._table = self._table_from_metadata(metadata.get('_table', {}))

    @property
    def name(self) -> str:
        return self._metadata['ClassName']

    @property
    def has_key_index(self) -> bool:
        return 'HasKeyIndex' in self._metadata and self._metadata['HasKeyIndex'] == '1'

    @property
    def metadata(self) -> dict:
        metadata = dict(self._metadata)
        if self._table:
            metadata['_table'] = self._table.metadata
        return metadata

    @property
    def table(self) -> Table:
        if not self._table:
            self._table = self._fetch_table()
        return self._table

    def search(self,
               query: Union[str, Mapping[str, str]],
               fields: Sequence[str] = None,
               parse: bool = True,
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

        return SearchResult(
            count=result.count,
            max_rows=result.max_rows,
            data=tuple(Record(self, row, parse=parse) for row in result.data),
        )

    def _fetch_table(self) -> Table:
        table_metadata = self._http.get_metadata('table', resource=self.resource.name,
                                                 class_=self.name)[0].data
        return self._table_from_metadata(table_metadata)

    def _table_from_metadata(self, table_metadata: Sequence[dict]) -> Optional[Table]:
        if not table_metadata:
            return None
        return Table(self, table_metadata)

    def _validate_query(self, query: Union[str, Mapping[str, str]]) -> str:
        if isinstance(query, str):
            return query
        self._assert_fields(query)
        return ','.join('(%s=%s)' % (field, value) for field, value in query.items())

    def _validate_fields(self, fields: Sequence[str]) -> str:
        self._assert_fields(fields)
        return ','.join(fields)

    def _assert_fields(self, fields: Sequence[str]) -> None:
        permissible = self.table.fields
        invalid = tuple(f for f in fields if f not in permissible)
        if invalid:
            raise RetsClientError('invalid fields %s' % ','.join(invalid))

    def __repr__(self) -> str:
        return '<Class: %s:%s>' % (self.resource.name, self.name)
