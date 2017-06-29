from rets.http.client import RetsHttpClient


def get_metadata_data(http_client: RetsHttpClient, type_: str, **kwargs):
    metadata_structs = http_client.get_metadata(type_, **kwargs)
    if metadata_structs:
        return metadata_structs[0].data
    return ()
