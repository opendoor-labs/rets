from hashlib import md5
from typing import Any, Mapping, Sequence, Union
from urllib.parse import urljoin, urlsplit, urlunsplit, urlencode

import requests
from requests import Response
from requests.auth import AuthBase, HTTPBasicAuth, HTTPDigestAuth

from rets.http.parsers import (
    parse_capability_urls,
    parse_metadata,
    parse_object,
    parse_search,
    parse_system,
)
from rets.http.data import Object, Metadata, SearchResult, SystemMetadata
from rets.errors import RetsApiError, RetsClientError


class RetsHttpClient:

    def __init__(self,
                 login_url: str,
                 username: str = None,
                 password: str = None,
                 auth_type: str = 'digest',
                 user_agent: str = 'rets-python/0.3',
                 user_agent_password: str = '',
                 rets_version: str = '1.7.2',
                 capability_urls: str = None,
                 cookie_dict: dict = None,
                 use_get_method: bool = False,
                 ):
        self._user_agent = user_agent
        self._user_agent_password = user_agent_password
        self._rets_version = rets_version
        self._use_get_method = use_get_method

        splits = urlsplit(login_url)
        self._base_url = urlunsplit((splits.scheme, splits.netloc, '', '', ''))
        self._capabilities = capability_urls or {
            'Login': splits.path,
        }

        # Authenticate using either the user agent auth header and (basic or digest) HTTP auth.
        # SFARMLS (San Francisco) uses both methods together.
        if username and password:
            self._http_auth = _get_http_auth(username, password, auth_type)
        else:
            self._http_auth = None

        # we use a session to keep track of cookies that are required for certain MLSes
        self._session = requests.Session()

        # The user may provide an optional cookie_dict argument, which will be used on first login.
        # When sending cookies (with a session_id) to the login url, the same cookie (session_id)
        # is returned, which (most likely) means no additional login is created.
        if cookie_dict:
            for name, value in cookie_dict.items():
                self._session.cookies.set(name, value=value)

        # this session id is part of the rets standard for use with a user agent password
        self._rets_session_id = ''

    @property
    def user_agent(self) -> str:
        """
        This header field contains information about the user agent originating the request.
        This is for statistical purposes, the tracing of protocol violations, and automated
        recognition of user agents for the sake of tailoring responses to avoid particular user
        agent limitations, as well as providing enhanced capabilities to some user-agents. All
        client requests MUST include this field. This is a standard HTTP header field as defined
        in RFC 2616.
        """
        return self._user_agent

    @property
    def rets_version(self) -> str:
        """
        The client MUST send the RETS-Version. The convention used is a "<major>.<minor>.<release>"
        numbering scheme similar to the HTTP Version in Section 3.1 of RFC 2616. The version of a
        RETS message is indicated by a RETS-Version field in the header of the message.
        """
        return 'RETS/' + self._rets_version

    @property
    def capability_urls(self) -> dict:
        return self._capabilities

    @property
    def cookie_dict(self) -> dict:
        """Keeps the last value in case of duplicate keys."""
        cookie_d = {}
        for k, v in self._session.cookies.iteritems():
            cookie_d[k] = v
        return cookie_d

    def login(self) -> dict:
        response = self._http_request(self._url_for('Login'))
        self._capabilities = parse_capability_urls(response)
        return self._capabilities

    def logout(self) -> None:
        self._http_request(self._url_for('Logout'))
        self._session = None

    def get_system_metadata(self) -> SystemMetadata:
        return parse_system(self._get_metadata('system'))

    def get_metadata(self,
                     type_: str,
                     resource: str = None,
                     class_: str = None,
                     metadata_id: str = '0',
                     ) -> Sequence[Metadata]:
        if resource:
            id_ = ':'.join(filter(None, [resource, class_]))
        else:
            id_ = metadata_id

        try:
            return parse_metadata(self._get_metadata(type_, id_))
        except RetsApiError as e:
            if e.reply_code in (20502, 20503):  # No metadata exists.
                return ()
            raise

    def _get_metadata(self, type_: str, metadata_id: str = '0') -> Response:
        """
        :param type_: The type of metadata being requested. The Type MUST begin with METADATA and
            may be one of the defined metadata types (see Section 11).

        :param metadata_id: If the last metadata_id is 0 (zero), then the request is for all Type
            metadata contained within that level; if the last metadata_id is '*', then the request
            is for all Type metadata contained within that level and all metadata Types contained
            within the requested Type. This means that for a metadata-id of METADATA-SYSTEM, for
            example, the server is expected to return all metadata.

            Note: The metadata_id for METADATA-SYSTEM and METADATA-RESOURCE must be 0 or *.
        """
        payload = {
            'Type': 'METADATA-' + type_.upper(),
            'ID': metadata_id,
            'Format': 'COMPACT',
        }
        return self._http_request(self._url_for('GetMetadata'), payload=payload)

    def search(self,
               resource: str,
               class_: str,
               query: str,
               select: str = None,
               count: int = 1,
               limit: int = None,
               offset: int = 1,
               restricted_indicator: str = None,
               standard_names: bool = False,
               query_type: str = 'DMQL2',
               format_: str = 'COMPACT-DECODED',
               ) -> SearchResult:
        """
        The Search transaction requests that the server search one or more searchable databases
        and return the list of qualifying records. The body of the response contains the records
        matching the query, presented in the requested format.

        :param resource: The type of search to perform as discussed in Section 7.1 and defined
            in the Metadata (see section 11.2.2).

        :param class_: This parameter is set to a value that represents the class of data within
            the resource, taken from the Class metadata (section 11.3.1). If the resource has no
            classes, the class_ parameter will be ignored by the server and may be omitted by the
            client. If the client does include the class_ parameter for a classless search, the
            value should be the same as the resource in order to insure forward compatibility.

        :param query:

        :param count: If this argument is set to one '1', then a record-count is returned in the
            response in addition to the data. Note that on some servers this will cause the
            search to take longer since the count must be returned before any records are
            received. If this entry is set to two '2' then only a record-count is returned; no
            data is returned, but all matches are counted regardless of any Offset or Limit
            parameter. If the Count argument is not present or set to zero '0' then no record
            count is returned.

        :param limit:

        :param offset:

        :param restricted_indicator:

        :param standard_names: Queries may use either standard names or system names in the query
            (Section 7.7). If the client chooses to use standard names, it must indicate this
            using the standard_names argument. If this entry is set to '0' or is not present the
            field names passed in the search are the SystemNames, as defined in the metadata. If
            this entry is set to '1' then the StandardNames are used for the field names passed
            in the search. The StandardName designation applies to all names used in the query:
            SearchType, Class, Query and Select.

        :param format_: 'COMPACT' means a field list <COLUMNS> followed by a delimited set of the
            data fields <DATA>. 'COMPACT-DECODED' is the same as COMPACT except the data for any
            field with an interpretation of Lookup, LookupMulti, LookupBitString or LookupBitMask,
            is returned in a fully-decoded format using the LongValue. See Section 13 for more
            information on the COMPACT formats and section 11.4.3 for more information on the
            Lookup types. 'STANDARD-XML' means an XML presentation of the data in the format
            defined by the RETS Data XML DTD. Servers MUST support all formats. If the format is
            not specified, the server MUST return STANDARD-XML.
        """
        raw_payload = {
            'SearchType': resource,
            'Class': class_,
            'Query': query,
            'QueryType': query_type,
            'Select': select,
            'Count': count,
            'Limit': limit or 'NONE',
            'Offset': offset,
            'RestrictedIndicator': restricted_indicator,
            'StandardNames': int(standard_names),
            'Format': format_,
        }
        # None values indicate that the argument should be omitted from the request
        payload = {k: v for k, v in raw_payload.items() if v is not None}

        response = self._http_request(self._url_for('Search'), payload=payload)
        return parse_search(response)

    def get_object(self,
                   resource: str,
                   object_type: str,
                   resource_keys: Union[str, Mapping[str, Any], Sequence[str]],
                   media_types: Union[str, Sequence[str]] = '*/*',
                   location: bool = False,
                   ) -> Sequence[Object]:
        """
        The GetObject transaction is used to retrieve structured information related to known
        system entities. It can be used to retrieve multimedia files and other key-related
        information. Objects requested and returned from this transaction are requested and
        returned as MIME media types. The message body for successful retrievals contains only
        the objects in the specified MIME media type. Error responses follow the normal response
        format (section 3.9).

        :param resource: A resource defined in the metadata dictionary (see Section 11.2.2). The
            resource from which the object should be retrieved is specified by this entry. For
            more information see 5.9. The resource must be a resource defined in the metadata
            (section 11.4.1).

        :param object_type: The object type as defined in the metadata (see Section 11.4.1). The
            grouping category to which the object belongs. The type must be an ObjectType defined
            in the Object metadata for this Resource. For more information see section 11.4.1.

        :param resource_keys: A single value or a list-like or dict-like container specifying the
            entities of the resource to retrieve objects for, where the entity is given by the
            KeyField of the resource. If the resource_ids is a value or is list-like, then all
            objects corresponding to the entities are returned by default. If resource_ids is
            dict-like, then it is a mapping from the resource entity to an object_id_list.

            The object_id_list can take the values: '*', 0, or an array of positive ids. If it is
            '*', then all objects are returns. If it is 0, then the preferred object is returned.
            Otherwise, the ids will refer to the sequential index of the objects beginning with 1.

        :param media_types: A single or list-like container of acceptable media types for the
            server to return. If media_types is like-like, then the ordering specifies the
            preference of the media types to return, with the first being the most desirable. If
            the server is unable to provide the requested media type, it should return a 406
            Not Acceptable status, or if no objects exist for any media type then the server
            should return a 404 Not Found.

        :param location: Flag to indicate whether the object or a URL to the object should be
            returned. If location is set to True, it is up to the server to support this
            functionality and the lifetime of the returned URL is not given by the RETS
            specification.
        """
        headers = {
            'Accept': _build_accepted_media_types(media_types),
        }
        payload = {
            'Resource': resource,
            'Type': object_type,
            'ID': _build_entity_object_ids(resource_keys),
            'Location': int(location),
        }
        response = self._http_request(self._url_for('GetObject'), headers=headers, payload=payload)
        return parse_object(response)

    def _url_for(self, transaction: str) -> str:
        try:
            url = self._capabilities[transaction]
        except KeyError:
            raise RetsClientError('No URL found for transaction %s' % transaction)
        return urljoin(self._base_url, url)

    def _http_request(self, url: str, headers: dict = None, payload: dict = None) -> Response:
        if not self._session:
            raise RetsClientError('Session not instantiated. Call .login() first')

        request_headers = {
            **(headers or {}),
            'User-Agent': self.user_agent,
            'RETS-Version': self.rets_version,
            'RETS-UA-Authorization': self._rets_ua_authorization()
        }

        if self._use_get_method:
            if payload:
                url = '%s?%s' % (url, urlencode(payload))
            response = self._session.get(url, auth=self._http_auth, headers=request_headers)
        else:
            response = self._session.post(url, auth=self._http_auth, headers=request_headers, data=payload)

        response.raise_for_status()
        self._rets_session_id = self._session.cookies.get('RETS-Session-ID', '')
        return response

    def _rets_ua_authorization(self) -> str:
        return 'Digest ' + self._user_agent_auth_digest()

    def _user_agent_auth_digest(self) -> str:
        user_password = '%s:%s' % (self.user_agent, self._user_agent_password)
        a1 = md5(user_password.encode()).hexdigest()

        digest_values = '%s::%s:%s' % (a1, self._rets_session_id, self.rets_version)
        return md5(digest_values.encode()).hexdigest()


def _get_http_auth(username: str, password: str, auth_type: str) -> AuthBase:
    if auth_type == 'basic':
        return HTTPBasicAuth(username, password)
    if auth_type == 'digest':
        return HTTPDigestAuth(username, password)
    raise RetsClientError('unknown auth type %s' % auth_type)


def _build_entity_object_ids(entities: Union[str, Mapping[str, Any], Sequence[str]]) -> str:
    """
    Builds the string of object ids as required by the GetObject transaction request. See
    section 5.3 for the full definition:

    ID              ::= resource-set *(, resource-set)
    resource-set    ::= resource-entity [: object-id-list]
    resource-entity ::= 1*ALPHANUM
    object-id-list  ::= * | object-id *(: object-id)
    object-id       ::= 1*5DIGIT
    """
    if isinstance(entities, str):
        return _build_entity_object_ids((entities,))
    elif isinstance(entities, Sequence):
        return _build_entity_object_ids({e: '*' for e in entities})
    elif not isinstance(entities, Mapping):
        raise RetsClientError('Invalid entities argument')

    def _build_object_ids(object_ids: Any) -> str:
        if object_ids in ('*', 0, '0'):
            return str(object_ids)
        elif isinstance(object_ids, Sequence):
            return ':'.join(str(o) for o in object_ids)
        else:
            raise RetsClientError('Invalid entities argument')

    return ','.join('%s:%s' % (entity, _build_object_ids(object_ids))
                    for entity, object_ids in entities.items())


def _build_accepted_media_types(media_types: Union[str, Sequence[str]]) -> str:
    """
    Builds the Accept header of media types as required by the GetObject transaction request.
    The qvalue is used to specify the desirability of a given media type with 1 being the most
    desirable, 0 being the least, and a range in between.
    See section 5.1 for the full definition:

    Accept    ::= type / subtype [; parameter] *(, type / subtype [; parameter])
    type      ::= * | <publicly defined type>
    subtype   ::= * | <publicly defined subtype>
    parameter ::= q = <qvalue scale from 0 to 1>

    A complete list of media types is available at http://www.iana.org/assignments/media-types.
    """
    if isinstance(media_types, str):
        return media_types
    elif not isinstance(media_types, Sequence):
        raise RetsClientError('Invalid media types argument')

    n = float(len(media_types))
    return ','.join('%s;%.4f' % (types, 1 - i / n) for i, types in enumerate(media_types))
