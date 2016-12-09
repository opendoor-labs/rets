from typing import Optional, Sequence

from rets.client.resource import Resource
from rets.http import RetsHttpClient


class RetsClient:

    def __init__(self, *args, http_client: RetsHttpClient = None, metadata: dict = None, **kwargs):
        self._http = http_client or RetsHttpClient(*args, **kwargs)
        self._http.login()
        self._metadata = metadata or {}

    @property
    def resources(self) -> Sequence[Resource]:
        if '_resources' not in self._metadata:
            self._metadata['_resources'] = self._fetch_resources()
        return self._metadata['_resources']

    def get_resource(self, name: str) -> Optional[Resource]:
        for resource in self.resources:
            if resource.name == name:
                return resource
        return None

    def _fetch_resources(self) -> Sequence[Resource]:
        metadata = self._http.get_metadata('resource')[0].data
        return tuple(Resource(m, self._http) for m in metadata)
