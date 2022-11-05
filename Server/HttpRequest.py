class HttpRequest:
    """
    Creates HTTP request from string
    """
    def __init__(self, data):
        # parse data
        lines = data.split("\r\n")
        request_line = lines[0].split(" ")
        self.method = request_line[0]
        self.path = request_line[1]
        self.protocol = request_line[2]
        # header values in dictionary
        self.headers = {}
        for line in lines[1:]:
            if line == "":
                break
            header, value = line.split(": ")
            self.headers[header] = value
        self.body = ""
        for line in lines[lines.index("") + 1:]:
            self.body += line

    def __str__(self):
        return f"{self.method} {self.path} {self.protocol}\r\n" + \
               "\r\n".join([f"{k}: {v}" for k, v in self.headers.items()]) + \
               "\r\n\r\n" + \
               self.body

    def query(self):
        """
        Returns query string
        :return: (Dictionary), empty if not query in http request path, else returns dictionary of query split by '&'
        """
        if "?" not in self.path:
            return {}
        query_string = self.path.split("?")[1]
        query = {}
        for pair in query_string.split("&"):
            key, value = pair.split("=")
            query[key] = value
        return query

