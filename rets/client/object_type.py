from typing import Any, Mapping, Sequence, Union

from rets.http import Object, RetsHttpClient


class ObjectType:

    def __init__(self, resource, metadata: dict, http_client: RetsHttpClient):
        self.resource = resource
        self._http = http_client
        self._metadata = metadata

    @property
    def name(self) -> str:
        return self._metadata['ObjectType']

    @property
    def mime_type(self) -> str:
        if 'MIMEType' in self._metadata:
            return self._metadata['MIMEType']
        return self._metadata['MimeType']

    @property
    def metadata(self) -> dict:
        return dict(self._metadata)

    def get(self, resource_keys: Union[str, Mapping[str, Any], Sequence[str]],
            **kwargs) -> Sequence[Object]:
        return self._http.get_object(self.resource.name, self.name, resource_keys, **kwargs)

    def __repr__(self) -> str:
        return '<Object: %s:%s>' % (self.resource.name, self.name)
