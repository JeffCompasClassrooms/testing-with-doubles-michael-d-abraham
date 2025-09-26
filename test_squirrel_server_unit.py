import io
import json
import pytest
from squirrel_server import SquirrelServerHandler
from squirrel_db import SquirrelDB


# working through examples


class FakeRequest:
    def __init__(self, mock_wfile, method, path, body=None):
        self._mock_wfile = mock_wfile
        self._method = method
        self._path = path
        self._body = body

    def sendall(self, _):
        return

    def makefile(self, *args, **kwargs):
        # args[0] == 'rb' for reading request, 'wb' for writing response
        if args[0] == 'rb':
            if self._body is not None:
                headers = f'Content-Length: {len(self._body)}\r\n'
                body = self._body
            else:
                headers = ''
                body = ''
            raw = f'{self._method} {self._path} HTTP/1.0\r\n{headers}\r\n{body}'
            return io.BytesIO(raw.encode('utf-8'))
        elif args[0] == 'wb':
            return self._mock_wfile

