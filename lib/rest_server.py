from __future__ import annotations

import http.server
import http.cookies
import json
import os
import shutil
import sys
import urllib.parse
from typing import *

class RESTRequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, restServer:RESTServer, *args, **kwargs):
        self.restServer = restServer
        http.server.BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def do_HEAD(self):
        self.handle_method('HEAD')

    def do_GET(self):
        self.handle_method('GET')

    def do_POST(self):
        self.handle_method('POST')

    def do_PUT(self):
        self.handle_method('PUT')

    def do_DELETE(self):
        self.handle_method('DELETE')

    def _server(self) -> RESTServer:
        return self.restServer

    @staticmethod
    def _guess_media_type(file:str) -> Optional[str]:
        if file.endswith(".js"):
            return "text/javascript"
        elif file.endswith(".css"):
            return "text/css"
        elif file.endswith(".html"):
            return "text/html"
        else:
            return None

    def _handle_file_requests(self, method:str) -> bool:
        if self._server().fileRoot is None:
            # If file requests aren't enabled, don't do anything
            return False

        # Check if this looks like a file request
        if self.path == "/" or self.path.startswith("/" + self._server().filePathPrefix + "/"):
            subPath = self._server().indexFile if self.path == "/" else self.path[6:]
            fullFilePath = os.path.join(self._server().fileRoot, subPath)

            if method == 'GET':
                try:
                    f = open(os.path.join(fullFilePath), "rb")
                    try:
                        self.send_response(200)

                        mediaType = self._guess_media_type(subPath)
                        if mediaType is not None:
                            self.send_header('Content-type', mediaType)

                        self.end_headers()
                        shutil.copyfileobj(f, self.wfile)
                    finally:
                        f.close()
                except Exception as e:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write('File not found\n'.encode())
            else:
                self.send_response(405)
                self.end_headers()
                self.wfile.write('Only GET is supported\n'.encode())

            # Indicate that we handled the request (success or not)
            return True
        else:
            return False

    def handle_method(self, method) -> None:
        if not self._handle_file_requests(method):
            request = self._get_request()
            route = self._get_route(request)
            if route is None:
                self.send_response(404)
                self.end_headers()
                self.wfile.write('Route not found\n'.encode())
            else:
                if method == 'HEAD':
                    self.send_response(200)
                    self.send_header('Content-type', route.media_type)
                    self.end_headers()
                else:
                    if method == route.method:

                        authorizationCheck = route.authorizationCheck if route.authorizationCheck is not None else self._server().defaultAuthorizationCheck
                        if authorizationCheck is not None:
                            if not authorizationCheck(request):
                                self.send_response(401)
                                self.end_headers()
                                self.wfile.write('Client is not authorized\n'.encode())
                                return

                        response = RESTResponse()
                        result = route.handle(request, response)

                        self.send_response(200)

                        for keyword, value in response.headers.items():
                            self.send_header(keyword, value)

                        self.send_header('Content-type', route.media_type)
                        self.end_headers()

                        if result is None:
                            result = "".encode()
                        elif route.media_type == "application/json":
                            result = json.dumps(result).encode()
                        elif isinstance(result, str):
                            result = result.encode()

                        self.wfile.write(result)

                    else:
                        self.send_response(405)
                        self.end_headers()
                        self.wfile.write(method + ' is not supported\n'.encode())

    def _get_request(self) -> RESTRequest:
        return RESTRequest(self)

    def _get_route(self, request) -> Optional[RESTRoute]:
        return self._server().routes.get(request.path)


class RESTRoute:
    def __init__(self, method:str, route:str, media_type:str, handler:Callable[..., Any], authorizationCheck:Optional[Callable[[RESTRequest], bool]]=None):
        self.method = method
        self.route = route
        self.media_type = media_type
        self.handler = handler
        self.authorizationCheck = authorizationCheck

    def handle(self, request:RESTRequest, response:RESTResponse):
        # TODO: Implement automatic type conversions for basic types using https://stackoverflow.com/questions/49560974/inspect-params-and-return-types
        #       (will need to pass the original handler here though)
        return self.handler(request, response, **request.parameters)


class RESTRequest:
    def __init__(self, requestHandler:RESTRequestHandler):
        parsed = urllib.parse.urlparse(requestHandler.path)
        self.path:str = parsed.path

        parsedQuery = urllib.parse.parse_qs(parsed.query)

        self.parameters:Dict[str, str] = {}
        for key, values in parsedQuery.items():
            self.parameters[key] = values[0]

        cookiesHeader = requestHandler.headers.get("Cookie")
        if cookiesHeader is not None:
            self.cookies = http.cookies.SimpleCookie(cookiesHeader)
        else:
            self.cookies = http.cookies.SimpleCookie("")

class RESTResponse:
    def __init__(self):
        self.headers:Dict[str, str] = {}

    def add_header(self, keyword, value):
        self.headers[keyword] = value

class RESTServer:
    def __init__(self, port:int=8080):
        self.server:http.server.HTTPServer = None
        self.routes:Dict[str, RESTRoute] = {}
        self.fileRoot:str = None
        self.indexFile:str = None
        self.filePathPrefix:str = None
        self.port = port
        self._create_server(port)
        self.defaultAuthorizationCheck:Optional[Callable[[], bool]] = None

    def _create_server(self, port:int) -> None:
        self.server = http.server.HTTPServer(('', port), (lambda *args, **kwargs: RESTRequestHandler(self, *args, **kwargs)))
        self.service_actions = lambda:None
        self.server.timeout = 0.05

    def enable_file_access(self, root:str=None, indexFile:str="index.html", prefix:str="file") -> None:
        if root is None:
            root = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "web")

        self.fileRoot = root
        self.indexFile = indexFile
        self.filePathPrefix = prefix

    def add_function(self, route:str, handler:Callable[..., Any], method:str= "POST", media_type:str= "application/json", authorizationCheck:Optional[Callable[[RESTRequest], bool]]=None) -> None:
        self.routes["/" + route] = RESTRoute(method, "/" + route, media_type, (lambda request, response, *args, **kwargs: handler(*args, **kwargs)), authorizationCheck)

    def add_extended_function(self, route:str, handler:Callable[..., Any], method:str= "POST", media_type:str= "application/json", authorizationCheck:Optional[Callable[[RESTRequest], bool]]=None) -> None:
        self.routes["/" + route] = RESTRoute(method, "/" + route, media_type, handler, authorizationCheck)

    def serve_forever(self, poll_interval=0.1):
        self.server.serve_forever(poll_interval)

    def serve_once(self):
        self.server.handle_request()

    def server_close(self):
        self.server.server_close()
