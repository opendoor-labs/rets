from typing import Sequence

from rets.http import Object


class Record:

    def __init__(self, resource_class, data: dict):
        self.resource_class = resource_class
        self.data = data

    def __repr__(self) -> str:
        return '<Record: %s:%s>' % (
            self.resource_class.resource.name,
            self.resource_class.name,
        )
