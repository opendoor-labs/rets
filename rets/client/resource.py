from typing import Optional, Sequence

from rets.client.resource_class import ResourceClass
from rets.client.object_type import ObjectType
from rets.http import RetsHttpClient


class Resource:

    def __init__(self, metadata: dict, http_client: RetsHttpClient):
        self._http = http_client
        self._metadata = metadata

    @property
    def name(self) -> str:
        return self._metadata['ResourceID']

    @property
    def key_field(self) -> str:
        return self._metadata['KeyField']

    @property
    def classes(self) -> Sequence[ResourceClass]:
        if '_classes' not in self._metadata:
            self._metadata['_classes'] = self._fetch_classes()
        return self._metadata['_classes']

    def get_class(self, name: str) -> Optional[ResourceClass]:
        for resource_class in self.classes:
            if resource_class.name == name:
                return resource_class
        return None

    @property
    def object_types(self) -> Sequence[ObjectType]:
        if '_object_types' not in self._metadata:
            self._metadata['_object_types'] = self._fetch_object_types()
        return self._metadata['_object_types']

    def get_object_type(self, name: str) -> Optional[ObjectType]:
        for resource_object in self.object_types:
            if resource_object.name == name:
                return resource_object
        return None

    def _fetch_classes(self) -> Sequence[ResourceClass]:
        metadata = self._http.get_metadata('class', resource=self.name)[0].data
        return tuple(ResourceClass(self, m, self._http) for m in metadata)

    def _fetch_object_types(self) -> Sequence[ObjectType]:
        metadata = self._http.get_metadata('object', resource=self.name)[0].data
        return tuple(ObjectType(self, m, self._http) for m in metadata)

    def __repr__(self) -> str:
        return '<Resource: %s>' % self.name
