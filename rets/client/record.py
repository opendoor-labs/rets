from typing import Sequence

from rets.http import Object


class Record:

    def __init__(self, resource_class, data: dict, parse: bool = True):
        self._resource_class = resource_class

        self._raw_data = data
        self._data = self._resource_class.table.parse(data) if parse else data

        self.__key__ = str(data[resource_class.resource.key_field])

    def get_objects(self, name: str) -> Sequence[Object]:
        resource_object = self._resource_class.resource.get_object(name)
        return resource_object.get(self.__key__)

    def __getattr__(self, name: str):
        return self._data[name]

    def __repr__(self) -> str:
        return '<Record: %s:%s:%s>' % (
            self._resource_class.resource.name,
            self._resource_class.name,
            self.__key__,
        )
