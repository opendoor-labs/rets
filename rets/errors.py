
class RetsError(RuntimeError):
    pass


class RetsClientError(RetsError):
    pass


class RetsParseError(RetsClientError):
    pass


class RetsResponseError(RetsClientError):

    def __init__(self, content: str, headers: dict):
        super().__init__('Unexpected response from RETS')
        self.content = content
        self.headers = headers


class RetsApiError(RetsClientError):

    def __init__(self, reply_code: int, reply_text: str, xml: str):
        super().__init__('[%i] %s\n\n%s' % (reply_code, reply_text, xml))
        self.reply_code = reply_code
        self.reply_text = reply_text
        self.xml = xml
