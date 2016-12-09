
class RetsError(RuntimeError):
    pass


class RetsClientError(RetsError):
    pass


class RetsParseError(RetsClientError):
    pass


class RetsApiError(RetsClientError):

    def __init__(self, reply_code: int, reply_text: str, xml: str):
        super().__init__('[%i] %s\n\n%s' % (reply_code, reply_text, xml))
        self.reply_code = reply_code
        self.reply_text = reply_text
        self.xml = xml
