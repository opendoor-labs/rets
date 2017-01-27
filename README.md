[![PyPI Version](https://badge.fury.io/py/rets-python.svg)](https://pypi.python.org/pypi/rets-python)
[![Code Health](https://landscape.io/github/opendoor-labs/rets/master/landscape.svg?style=flat)](https://landscape.io/github/opendoor-labs/rets/master)
[![Build Status](https://travis-ci.org/opendoor-labs/rets.svg?branch=master)](https://travis-ci.org/opendoor-labs/rets)
[![Python Version](https://img.shields.io/pypi/pyversions/rets-python.svg)](https://pypi.python.org/pypi/rets-python)
[![License](https://img.shields.io/pypi/l/rets-python.svg)](https://pypi.python.org/pypi/rets-python)

# RETS Python 3 Client

Python 3 client for the Real Estate Transaction Standard (RETS) Version 1.7.2. Supports Python 3.3 or later.

```
pip install rets-python
```

## Example

Standard usage

```python
>>> from rets.client import RetsClient

>>> client = RetsClient(
    login_url='http://my.rets.server/rets/login',
    username='username',
    password='password',
    # Alternatively authenticate using user agent password
    # user_agent='rets-python/0.3',
    # user_agent_password=''
)

>>> resource = client.get_resource('Property')
>>> resource.key_field
'LIST_1'

>>> resource_class = resource.get_class('A')
>>> resource_class.has_key_index
True

>>> photo_object_type = resource.get_object_type('HiRes')
>>> photo_object_type.mime_type
'image/jpeg'
```

You can retrieve listings by performing a search query on the ResourceClass object. The results
will include any associated search metadata.

```python
>>> search_result = resource_class.search(query='(LIST_87=2017-01-01+)', limit=10)
>>> search_result.count
11941
>>> search_result.max_rows
False
>>> len(search_result.data)
10
```

Photos and other object types for a record can be retrieved directly from the record object. They
can also be retrieved in bulk from the ObjectType object using the resource keys of the records.

```python
>>> listing = search_result.data[0]
>>> listing.resource_key
'20170104191513476022000000'
>>> listing.get_objects('HiRes', location=True)
(Object(mime_type='image/jpeg', content_id='20170104191513476022000000', description='Front', object_id='1', url='...', preferred=True, data=None), ...)

>>> all_photos = photo_object_type.get(
    resource_keys=[listing.resource_key for listing in listings],
    location=True,
)
>>> len(all_photos)
232
>>> all_photos[0]
Object(mime_type='image/jpeg', content_id='20071218141725529770000000', description='Primary Photo', object_id='1', url='...', preferred=True, data=None)
```

Low level RETS HTTP client usage:

```python
from rets.http import RetsHttpClient

client = RetsHttpClient(
    login_url='http://my.rets.server/rets/login',
    username='username',
    password='password',
    # Alternatively authenticate using user agent password
    # user_agent='rets-python/0.3',
    # user_agent_password=''
)

# Authenticate and fetch available transactions
client.login()

# See available Resources
client.get_metadata('resource')

# See available Classes for the Property resource
client.get_metadata('class', resource='Property')

# See the Table definition for Class A
client.get_metadata('table', resource='Property', class_='A')

# Get a sample of recent listings
search_result = client.search(
    resource='Property',
    class_='A',
    query='(LIST_87=2017-01-01+)',
    select='LIST_87,LIST_105,LIST_1',
    limit=10,
    count=1,
)

# Get the KeyField values of the listings
resource_keys = [r['LIST_1'] for r in search_result.data]

# Fetch the photo URLs for those recent listings
objects = client.get_object(
    resource='Property',
    object_type='HiRes',
    resource_keys=resource_keys,
    location=True,
)
```
