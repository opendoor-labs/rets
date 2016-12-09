from collections import OrderedDict
from itertools import zip_longest
from typing import Iterable, Sequence

from bs4 import Tag
from requests import Response

from rets.http.data import Metadata, Object, SearchResult, SystemMetadata
from rets.http.parsers.http import parse_xml, parse_response
from rets.errors import RetsParseError, RetsApiError


def parse_capability_urls(response: Response) -> dict:
    """
    Parses the list of capability URLs from the response of a successful Login transaction.

    The capability url list is the set of functions or URLs to which the Login grants access.
    A capability consists of a key and a URL. The list returned from the server in the login
    reply must include URLs for Search, Login, and GetMetadata, and optionally may include
    URLs for Action, ChangePassword, GetObject, LoginComplete, Logout, ServerInformation,
    and Update.

    <RETS ReplyCode="0" ReplyText="Success">
        <RETS-RESPONSE>
            MemberName=member_name
            User=user_id,user_level,user_class,agent_code
            Broker=RETSOFFIC
            MetadataVersion=01.09.02991
            MetadataTimestamp=2016-11-24T05:24:06Z
            MinMetadataTimestamp=2016-11-24T05:24:06Z
            Login=/rets2_1/Login
            Search=/rets2_1/Search
            GetMetadata=/rets2_1/GetMetadata
            X-SampleLinks=/rets2_1/Links
            X-SupportSite=http://flexmls.com/rets/
            X-NotificationFeed=http://retsgw.flexmls.com/atom/feed/private/atom.xml
            GetObject=/rets2_1/GetObject
            Logout=/rets2_1/Logout
            X-ApiAccessSettings=/rets2_1/API
        </RETS-RESPONSE>
    </RETS>
    """
    tag = parse_xml(response)
    response_tag = tag.find('RETS-RESPONSE')
    if response_tag is None:
        return {}
    raw_arguments = response_tag.text.strip().split('\n')
    return dict((s.strip() for s in arg.split('=', 1)) for arg in raw_arguments)


def parse_metadata(response: Response) -> Sequence[Metadata]:
    """
    Parse the information from a GetMetadata transaction.

    <METADATA-RESOURCE Date="2016-11-24T05:24:06Z" Version="01.09.02991">
        <COLUMNS>	ResourceID	StandardName	</COLUMNS>
        <DATA>	ActiveAgent	ActiveAgent	</DATA>
        <DATA>	Office	Office	</DATA>
        <DATA>	OpenHouse	OpenHouse	</DATA>
        <DATA>	Property	Property	</DATA>
        <DATA>	RentalSchedule	RentalSchedule	</DATA>
    </METADATA-RESOURCE>
    """
    tag = parse_xml(response)
    metadata_tags = tag.find_all(lambda t: t.name.startswith('METADATA-'))
    if metadata_tags is None:
        return ()

    def parse_metadata_tag(tag: Tag) -> Metadata:
        """ Parses a single <METADATA-X> tag """
        return Metadata(
            type_=tag.name.split('-', 1)[1],
            resource=tag.attrs.get('Resource'),
            class_=tag.attrs.get('Class'),
            data=tuple(_parse_data(tag)),
        )

    return tuple(parse_metadata_tag(metadata_tag) for metadata_tag in metadata_tags)


def parse_system(response: Response) -> SystemMetadata:
    """
    Parse the server system information from a SYSTEM GetMetadata transaction.

    <RETS ReplyCode="0" ReplyText="Success">
        <METADATA-SYSTEM Date="2016-11-24T05:24:06Z" Version="01.09.02991">
            <SYSTEM SystemDescription="ARMLS" SystemID="az" TimeZoneOffset="-06:00"/>
            <COMMENTS/>
        </METADATA-SYSTEM>
    </RETS>
    """
    tag = parse_xml(response)
    metadata_system_tag = _find_or_raise(tag, 'METADATA-SYSTEM')
    system_tag = _find_or_raise(tag, 'SYSTEM')
    comments_tag = metadata_system_tag.find('COMMENTS')
    return SystemMetadata(
        system_id=system_tag.attrs['SystemID'],
        system_description=system_tag.attrs['SystemDescription'],
        system_date=metadata_system_tag.attrs['Date'],
        system_version=metadata_system_tag.attrs['Version'],

        # Optional fields
        time_zone_offset=system_tag.attrs.get('TimeZoneOffset'),
        comments=comments_tag and (comments_tag.text or None),
    )


def parse_search(response: Response) -> SearchResult:
    try:
        tag = parse_xml(response)
    except RetsApiError as e:
        if e.reply_code == 20201:  # No records found
            return SearchResult(0, False, ())
        raise

    count_tag = tag.find('COUNT')
    try:
        data = tuple(_parse_data(tag))
    except RetsParseError:
        data = None
    return SearchResult(
        count=count_tag and int(count_tag.attrs['Records']),
        max_rows=bool(tag.find('MAXROWS')),
        data=data,
    )


def parse_object(response: Response) -> Sequence[Object]:
    return parse_response(response)


def _parse_data(tag: Tag) -> Iterable[dict]:
    """
    Parses a generic container tag enclosing a single COLUMNS and multiple DATA tags, and returns
    a generator of dicts with keys given by the COLUMNS tag and values given by each DATA tag.
    The container tag may optionally contain a DELIMITER tag to define the delimiter used,
    otherwise a default of '\t' is assumed.

    <RETS ReplyCode="0" ReplyText="Success">
        <DELIMITER value="09"/>
        <COLUMNS>	LIST_87	LIST_105	LIST_1	</COLUMNS>
        <DATA>	2016-12-01T00:08:10	5489015	20160824051756837742000000	</DATA>
        <DATA>	2016-12-01T00:10:02	5497756	20160915055426038684000000	</DATA>
        <DATA>	2016-12-01T00:10:26	5528935	20161123230848928777000000	</DATA>
        <DATA>	2016-12-01T00:10:52	5528955	20161123234916869427000000	</DATA>
        <DATA>	2016-12-01T00:14:31	5530021	20161127221848669500000000	</DATA>
    </RETS>
    """
    delimiter = _parse_delimiter(tag)

    columns_tag = _find_or_raise(tag, 'COLUMNS')
    columns = _parse_data_line(columns_tag, delimiter)

    data_tags = tag.find_all('DATA')

    return (OrderedDict(zip_longest(columns, _parse_data_line(data, delimiter)))
            for data in data_tags)


def _find_or_raise(tag: Tag, child_tag_name: str) -> Tag:
    child = tag.find(child_tag_name)
    if child is None:
        raise RetsParseError('Missing %s tag' % child_tag_name)
    return child


def _parse_data_line(tag: Tag, delimiter: str = '\t') -> Sequence[str]:
    # DATA tags using the COMPACT format and COLUMN tags all start and end with delimiters
    return tag.text.split(delimiter)[1:-1]


def _parse_delimiter(tag: Tag) -> str:
    delimiter_tag = tag.find('DELIMITER')
    if delimiter_tag is None:
        return '\t'
    return chr(int(delimiter_tag.attrs['value']))
