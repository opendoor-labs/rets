from collections import namedtuple

Metadata = namedtuple('Metadata', (
    'type_',
    'resource',
    'class_',
    'data',
))

Object = namedtuple('Object', (
    'mime_type',
    'content_id',
    'description',
    'object_id',
    'url',
    'preferred',
    'data',
))

SearchResult = namedtuple('SearchResult', (
    'count',
    'max_rows',
    'data',
))

SystemMetadata = namedtuple('SystemMetadata', (
    'system_id',
    'system_description',
    'system_date',
    'system_version',
    'time_zone_offset',
    'comments',
))
