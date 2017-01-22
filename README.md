[![PyPI Version](https://badge.fury.io/py/rets-python.svg)](https://pypi.python.org/pypi/rets-python/)
[![Code Health](https://landscape.io/github/opendoor-labs/rets/master/landscape.svg?style=flat)](https://landscape.io/github/opendoor-labs/rets/master)
[![Build Status](https://travis-ci.org/opendoor-labs/rets.svg?branch=master)](https://travis-ci.org/opendoor-labs/rets)

# RETS Python 3 Client

Python 3 client for the Real Estate Transaction Standard (RETS) Version 1.7.2. Supports Python 3.3 or later.

```
pip install rets-python
```

## Example

Standard usage

```python
from rets.client import RetsClient

client = RetsClient(
    username='',
    password='',
    base_url='http://my.rets.server',
    login_url='/rets/login',
)

resource = client.get_resource('Property')
resource_class = resource.get_class('A')
photo_object_type = resource.get_object_type('HiRes')

# Perform a search query to retrieve some listings
search_result = resource_class.search(query='(LIST_87=1950-01-01+)', limit=100)
listings = search_result.data

# Retrieve photos for a single listing
listing = listings[0]
photos = listing.get_objects('HiRes', location=True)

# Or retrieve photos for all listings
all_photos = photo_object_type.get(resource_keys=[listing.__key__ for listing in listings])
```

Low level RETS HTTP client

```python
from rets.http import RetsHttpClient

client = RetsHttpClient(
    username='',
    password='',
    base_url='http://my.rets.server',
    login_url='/rets/login',
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
    query='(LIST_87=2016-12-05+)',
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
