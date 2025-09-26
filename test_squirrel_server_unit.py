# Unit tests for SquirrelServerHandler using test doubles only.
# No real HTTPServer, no real SQLite.

import io
import json
import pytest
from squirrel_server import SquirrelServerHandler
from squirrel_db import SquirrelDB



class FakeRequest:
    def __init__(self, mock_wfile, method, path, body=None):
        self._mock_wfile = mock_wfile
        self._method = method
        self._path = path
        self._body = body

    def sendall(self, _):
        return

    def makefile(self, *args, **kwargs):
        # 'rb' is what the handler reads (request line + headers + body)
        if args[0] == 'rb':
            headers = f'Content-Length: {len(self._body)}\r\n' if self._body else ''
            body = self._body or ''
            raw = f'{self._method} {self._path} HTTP/1.0\r\n{headers}\r\n{body}'
            return io.BytesIO(raw.encode('utf-8'))
        # 'wb' is what the handler writes the response body to
        elif args[0] == 'wb':
            return self._mock_wfile


# Fixtues 
@pytest.fixture
def dummy_client():
    return ('127.0.0.1', 80)

@pytest.fixture
def dummy_server():
    return None

# small write buffer i dont really get this but it works so cool
@pytest.fixture(autouse=True)
def patch_wbufsize(mocker):
    mocker.patch.object(SquirrelServerHandler, 'wbufsize', 1)

# makes sure that it  never open a real sqlite connection
@pytest.fixture
def mock_db_init(mocker):
    return mocker.patch.object(SquirrelDB, '__init__', return_value=None)

# Took these from the example thes are great
# read the doc and still only kinda got whats going on wit hthes 
@pytest.fixture
def mock_response_methods(mocker):
    mock_send_response = mocker.patch.object(SquirrelServerHandler, 'send_response')
    mock_send_header   = mocker.patch.object(SquirrelServerHandler, 'send_header')
    mock_end_headers   = mocker.patch.object(SquirrelServerHandler, 'end_headers')
    return mock_send_response, mock_send_header, mock_end_headers


# Tests
def describe_routing_for_unknown_resource():

    def it_returns_404_for_unknown_collection(mocker, mock_db_init, dummy_client, dummy_server, mock_response_methods):
        # GET /mike should route to handle404 vcause it doesn't exist
        req = FakeRequest(mocker.Mock(), 'GET', '/mike')

        handler = SquirrelServerHandler(req, dummy_client, dummy_server)

        send, hdr, end = mock_response_methods
        send.assert_called_once_with(404)
        hdr.assert_called_once_with("Content-Type", "text/plain")
        end.assert_called_once()
        handler.wfile.write.assert_called_once_with(b"404 Not Found")


def it_returns_404_when_put_has_no_id(mocker, mock_db_init, dummy_client, dummy_server, mock_response_methods):
    # PUT /squirrels (no id) should hit handle404 via do_PUT
    req = FakeRequest(mocker.Mock(), 'PUT', '/squirrels')

    handler = SquirrelServerHandler(req, dummy_client, dummy_server)

    send, hdr, end = mock_response_methods
    send.assert_called_once_with(404)
    hdr.assert_called_once_with("Content-Type", "text/plain")
    end.assert_called_once()
    handler.wfile.write.assert_called_once_with(b"404 Not Found")
