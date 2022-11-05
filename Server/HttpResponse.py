class HttpResponse:
    """
    Returns HTTP response
    """
    def __init__(self, status_code, body, content_type="text/html"):
        self.status_code = status_code
        self.body = body
        self.content_type = content_type

    def __str__(self):
        # TODO: if body is bytes of image
        return f"HTTP/1.1 {self.status_code}\r\n" + \
               f"Content-Type: {self.content_type}\r\n" + \
               f"Content-Length: {len(self.body)}\r\n" + \
               "\r\n" + \
               self.body
