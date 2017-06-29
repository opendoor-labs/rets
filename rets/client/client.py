from typing import Optional, Sequence

from rets.client.resource import Resource
from rets.client.utils import get_metadata_data
from rets.http import RetsHttpClient

"""
Example of metadata dict:

metadata = [{
    'ResourceID': 'Property',
    'KeyField': 'Matrix_Unique_ID',
    '_classes': [
        {
            'ClassName': 'Listing',
            'HasKeyIndex': '1',
            '_table': [
                ... column fields
            ],
        }
    ],
    '_object_types': [
        'ObjectType': 'LargePhoto',
        'MIMEType': 'image/jpeg',
    ]
}, {
    'ResourceID': 'Agent',
    'KeyField': 'Matrix_Unique_ID',
    '_classes': [
        {
            'ClassName': 'Listing',
            'HasKeyIndex': '1',
        }
    ],
}]
"""


class RetsClient:

    def __init__(self,
                 *args,
                 http_client: RetsHttpClient = None,
                 metadata: Sequence[dict] = (),
                 capability_urls: dict = None,
                 cookie_dict: dict = None,
                 **kwargs):
        self.http = http_client or RetsHttpClient(*args,
                                                  capability_urls=capability_urls, cookie_dict=cookie_dict,
                                                  **kwargs)
        if not (capability_urls and cookie_dict):
            self.http.login()
        self._resources = self._resources_from_metadata(metadata)

    @property
    def metadata(self) -> Sequence[dict]:
        return tuple(resource.metadata for resource in self._resources)

    @property
    def resources(self) -> Sequence[Resource]:
        if not self._resources:
            # TODO(ML) Differentiate between not having the metadata and
            # having an empty metadata
            self._resources = self._fetch_resources()
        return self._resources

    def get_resource(self, name: str) -> Optional[Resource]:
        for resource in self.resources:
            if resource.name == name:
                return resource
        raise KeyError('unknown resource %s' % name)

    def _fetch_resources(self) -> Sequence[Resource]:
        metadata = get_metadata_data(self.http, 'resource')
        return self._resources_from_metadata(metadata)

    def _resources_from_metadata(self, metadata: Sequence[dict]) -> Sequence[Resource]:
        return tuple(Resource(m, self.http) for m in metadata)
