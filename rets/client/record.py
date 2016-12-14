from typing import Sequence

from rets.http import Object


class Record:

    def __init__(self, resource_class, data: dict, parse: bool = True):
        self.resource_class = resource_class
        self.key_value = str(data[resource_class.resource.key_field])
        self.data = self.resource_class.table.parse(data) if parse else data
        self._raw_data = data

    def get_objects(self, name: str) -> Sequence[Object]:
        resource_object = self.resource_class.resource.get_object(name)
        return resource_object.get(self.key_value)

    def __repr__(self) -> str:
        return '<Record: %s:%s:%s>' % (
            self.resource_class.resource.name,
            self.resource_class.name,
            self.key_value,
        )
