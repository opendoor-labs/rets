from collections import OrderedDict
from itertools import zip_longest
from typing import Iterable, Sequence, Tuple, Union
from lxml import etree

from requests import Response
from requests_toolbelt.multipart.decoder import BodyPart

from rets.errors import RetsParseError, RetsApiError, RetsResponseError
from rets.http.data import Metadata, SearchResult, SystemMetadata

DEFAULT_ENCODING = 'utf-8'

ResponseLike = Union[Response, BodyPart]


def parse_xml(response: ResponseLike) -> etree.Element:
    encoding = response.encoding or DEFAULT_ENCODING
    root = etree.fromstring(response.content.decode(encoding), parser=etree.XMLParser(recover=True))

    if root is None:
        raise RetsResponseError(response.content, response.headers)

    reply_code, reply_text = _parse_rets_status(root)
    if reply_code and reply_text != "Operation Successful":
        raise RetsApiError(reply_code, reply_text, response.content)

    return root


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
            GetObject=/rets2_1/GetObject
            Logout=/rets2_1/Logout
        </RETS-RESPONSE>
    </RETS>
    """
    elem = parse_xml(response)
    response_elem = elem.find('RETS-RESPONSE')
    if response_elem is None:
        return {}
    raw_arguments = response_elem.text.strip().split('\n')
    return dict((s.strip() for s in arg.split('=', 1)) for arg in raw_arguments)


def parse_metadata(response: Response) -> Sequence[Metadata]:
    """
    Parse the information from a GetMetadata transaction.

    <RETS ReplyCode="0" ReplyText="Success">
        <METADATA-RESOURCE Date="2016-11-24T05:24:06Z" Version="01.09.02991">
            <COLUMNS>	ResourceID	StandardName	</COLUMNS>
            <DATA>	ActiveAgent	ActiveAgent	</DATA>
            <DATA>	Office	Office	</DATA>
            <DATA>	OpenHouse	OpenHouse	</DATA>
            <DATA>	Property	Property	</DATA>
            <DATA>	RentalSchedule	RentalSchedule	</DATA>
        </METADATA-RESOURCE>
    </RETS>
    """
    elem = parse_xml(response)
    metadata_elems = [e for e in elem.findall('*') if e.tag.startswith('METADATA-')]
    if metadata_elems is None:
        return ()

    def parse_metadata_elem(elem: etree.Element) -> Metadata:
        """ Parses a single <METADATA-X> element """
        return Metadata(
            type_=elem.tag.split('-', 1)[1],
            resource=elem.get('Resource'),
            class_=elem.get('Class'),
            data=tuple(_parse_data(elem)),
        )

    return tuple(parse_metadata_elem(metadata_elem) for metadata_elem in metadata_elems)


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
    elem = parse_xml(response)
    metadata_system_elem = _find_or_raise(elem, 'METADATA-SYSTEM')
    system_elem = _find_or_raise(metadata_system_elem, 'SYSTEM')
    comments_elem = metadata_system_elem.find('COMMENTS')
    return SystemMetadata(
        system_id=system_elem.get('SystemID'),
        system_description=system_elem.get('SystemDescription'),
        system_date=metadata_system_elem.get('Date'),
        system_version=metadata_system_elem.get('Version'),

        # Optional fields
        time_zone_offset=system_elem.get('TimeZoneOffset'),
        comments=comments_elem and (comments_elem.text or None),
    )


def parse_search(response: Response) -> SearchResult:
    try:
        elem = parse_xml(response)
    except RetsApiError as e:
        if e.reply_code == 20201:  # No records found
            return SearchResult(0, False, ())
        raise

    count_elem = elem.find('COUNT')
    if count_elem is not None:
        count = int(count_elem.get('Records'))
    else:
        count = None

    try:
        data = tuple(_parse_data(elem))
    except RetsParseError:
        data = None

    return SearchResult(
        count=count,
        # python xml.etree.ElementTree.Element objects are always considered false-y
        max_rows=elem.find('MAXROWS') is not None,
        data=data,
    )


def _parse_rets_status(root: etree.Element) -> Tuple[int, str]:
    """
    If RETS-STATUS exists, the client must use this instead
    of the status from the body-start-line
    """
    rets_status = root.find('RETS-STATUS')
    elem = rets_status if rets_status is not None else root
    return int(elem.get('ReplyCode')), elem.get('ReplyText')


def _parse_data(elem: etree.Element) -> Iterable[dict]:
    """
    Parses a generic container element enclosing a single COLUMNS and multiple DATA elems, and
    returns a generator of dicts with keys given by the COLUMNS elem and values given by each
    DATA elem. The container elem may optionally contain a DELIMITER elem to define the delimiter
    used, otherwise a default of '\t' is assumed.

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
    delimiter = _parse_delimiter(elem)

    columns_elem = _find_or_raise(elem, 'COLUMNS')
    columns = _parse_data_line(columns_elem, delimiter)

    data_elems = elem.findall('DATA')

    return (OrderedDict(zip_longest(columns, _parse_data_line(data, delimiter)))
            for data in data_elems)


def _find_or_raise(elem: etree.Element, child_elem_name: str) -> etree.Element:
    child = elem.find(child_elem_name)
    if child is None:
        raise RetsParseError('Missing %s element' % child_elem_name)
    return child


def _parse_data_line(elem: etree.Element, delimiter: str = '\t') -> Sequence[str]:
    # DATA elems using the COMPACT format and COLUMN elems all start and end with delimiters
    return elem.text.split(delimiter)[1:-1]


def _parse_delimiter(elem: etree.Element) -> str:
    delimiter_elem = elem.find('DELIMITER')
    if delimiter_elem is None:
        return '\t'
    return chr(int(delimiter_elem.get('value')))
