from typing import Optional, Sequence

from rets.client.resource_class import ResourceClass
from rets.client.object_type import ObjectType
from rets.client.utils import get_metadata_data
from rets.http import RetsHttpClient


class Resource:

    def __init__(self, metadata: dict, http_client: RetsHttpClient):
        self._http = http_client
        self._metadata = metadata
        self._classes = self._classes_from_metadata(metadata.get('_classes', ()))
        self._object_types = self._object_types_from_metadata(metadata.get('_object_types', ()))

    @property
    def name(self) -> str:
        return self._metadata['ResourceID']

    @property
    def key_field(self) -> str:
        return self._metadata['KeyField']

    @property
    def metadata(self) -> dict:
        metadata = dict(self._metadata)
        if self._classes:
            metadata['_classes'] = tuple(resource_class.metadata for resource_class in self._classes)
        if self._object_types:
            metadata['_object_types'] = tuple(object_type.metadata for object_type in self._object_types)
        return metadata

    @property
    def classes(self) -> Sequence[ResourceClass]:
        if not self._classes:
            self._classes = self._fetch_classes()
        return self._classes

    def get_class(self, name: str) -> Optional[ResourceClass]:
        for resource_class in self.classes:
            if resource_class.name == name:
                return resource_class
        raise KeyError('unknown class %s' % name)

    @property
    def object_types(self) -> Sequence[ObjectType]:
        if not self._object_types:
            self._object_types = self._fetch_object_types()
        return self._object_types

    def get_object_type(self, name: str) -> Optional[ObjectType]:
        for resource_object in self.object_types:
            if resource_object.name == name:
                return resource_object
        raise KeyError('unknown object type %s' % name)

    def _fetch_classes(self) -> Sequence[ResourceClass]:
        metadata = get_metadata_data(self._http, 'class', resource=self.name)
        return self._classes_from_metadata(metadata)

    def _fetch_object_types(self) -> Sequence[ObjectType]:
        metadata = get_metadata_data(self._http, 'object', resource=self.name)
        return self._object_types_from_metadata(metadata)

    def _classes_from_metadata(self, classes_metadata: Sequence[dict]) -> Sequence[ResourceClass]:
        return tuple(ResourceClass(self, m, self._http) for m in classes_metadata)

    def _object_types_from_metadata(self, object_types_metadata: Sequence[dict]) -> Sequence[ObjectType]:
        return tuple(ObjectType(self, m, self._http) for m in object_types_metadata)

    def __repr__(self) -> str:
        return '<Resource: %s>' % self.name
