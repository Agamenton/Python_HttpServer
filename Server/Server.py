import socket
import threading
import subprocess

from .HttpRequest import HttpRequest
from .HttpResponse import HttpResponse
from .WebsiteConfig import WebsiteConfig


MAX_SIZE = 1024


class Server:
    """
    Creates and starts new server object from list of websites of type WebsiteConfig
    Each website is dynamic or static
    """
    def __init__(self, websites=()):
        self.websites = websites
        self.process_ports = {}
        self.process_sockets = {}
        self.start()

    def __str__(self):
        return "".join([str(app) for app in self.websites])

    @staticmethod
    def from_config(config_file):
        """
        Creates server from config file
        :param config_file: path to config file
        :return: Server object
        """
        apps = []
        for line in config_file:
            app = line.split(';')
            apps.append(WebsiteConfig(app[0], app[1], app[2]))
        return Server(apps)

    def inject_website(self, website):
        """
        While server is already running, inject a new website to the server
        :param website: WebsiteConfig object
        :return: void
        """
        self.websites.append(website)
        self.assign_socket(website)
        if not website.is_static:
            self.start_dynamic_website(website)
        thread = threading.Thread(target=self.await_connection, args=website)
        thread.start()

    def start(self):
        """
        For each website in websites, assign socket to it and start listening on the socket
        if website is dynamic, start the process
        For each website in websites, start a thread that awaits connection on the socket
        :return: void
        """
        #Start server
        for website in self.websites:
            # create socket
            self.assign_socket(website)
            if not website.is_static:
                self.start_dynamic_website(website)

        for website in self.websites:
            thread = threading.Thread(target=self.await_connection, args=website)
            thread.start()

    def assign_socket(self, website: WebsiteConfig):
        """
        for given website, create socket and assign it to the website
        and start listening on the socket
        and add the socket to the process_sockets dictionary
        :param website: WebsiteConfig object
        :return: void
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((website.name, website.port))
        s.listen(website.max_users)
        self.process_sockets[website.name] = s

    def start_dynamic_website(self, website: WebsiteConfig):
        """
        Executes the run command for given website
        :param website: WebsiteConfig object
        :return: void (side effect, starts the process and adds it to the process_ports dictionary)
        """
        proc = subprocess.Popen(website.run_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        self.process_ports[website.port] = proc

    def await_connection(self, website: WebsiteConfig):
        """
        In loop waits for connection on the socket for given website
        if connection is established, start a thread that handles the client
        :param website: WebsiteConfig object
        :return: void (side effect, starts a thread that handles the client)
        """
        while True:
            conn, addr = self.process_sockets[website.name].accept()
            if conn:
                thread = threading.Thread(target=self.handle_client, args=(conn, addr, website))
                thread.start()

    def handle_client(self, conn, addr, website: WebsiteConfig):
        """
        Reads request from client and if any data were received passes it to handle_request method
        Then based on Connection header, closes the connection or keeps it open
        :param conn: socket connection
        :param addr: address of the client
        :param website: WebsiteConfig object
        :return: void
        """
        while True:
            http_request_string = conn.recv(MAX_SIZE)
            print("------------------------------------------------")
            # if user disconnected
            if not http_request_string:
                print("No data received")
                break

            print(http_request_string)
            http_request = HttpRequest(http_request_string)

            self.handle_request(conn, http_request, website)
            if http_request.headers["Connection"] == "close" or http_request.headers["Connection"] != "keep-alive":
                break

    def handle_request(self, conn, request: HttpRequest, website: WebsiteConfig):
        """
        If website is dynamic, send request to the website
        If website is static, send requested file to the client
        :param conn: socket connection
        :param request: HttpRequest object
        :param website: WebsiteConfig object
        :return: void
        """
        if website.is_static:
            self.handle_static_website_request(conn, website, request)
        else:
            self.handle_dynamic_website_request(conn, website, request)

    def handle_dynamic_website_request(self, conn, website, request):
        """
        Sends request to the website and receives response
        :param conn: socket connection
        :param website: WebsiteConfig object
        :param request: HttpRequest object
        :return: void (side effect, sends response to the client)
        """
        self.send_request_to_app(website, request)
        app_response = self.process_ports[website.port].stdout.readline() # TODO: read line in loop until the correct request was answered
        self.send_response_to_client(conn, app_response)

    def handle_static_website_request(self, conn, website, request):
        """
        Reads requested file from the disk and sends it to the client
        :param conn: socket connection
        :param request: HttpRequest object
        :return: void (side effect, sends response to the client)
        """
        requested_file = request.path
        try:
            app_response = self.get_file(requested_file, website)
            http_response = HttpResponse(200, app_response, "text/html") # TODO: change content type based on file extension
        except FileNotFoundError:
            http_response = HttpResponse(404, open("404.html", "rb").read(), "text/html")
        self.send_response_to_client(conn, http_response)

    def send_request_to_app(self, website, req):
        # TODO: send in loop until confirmation is received or timeout
        self.process_ports[website.port].stdin.write(req.to_bytes()) # TODO: also pass an ID of the request so we can match the response to the request

    def send_response_to_client(self, conn, response: HttpResponse):
        conn.sendall(str(response).encode("utf-8"))

    def get_file(self, file_path, website):
        try:
            with open(f"{website.path}{file_path}", "r") as file:
                return file.read()
        except FileNotFoundError:
            return "404 Not Found"
