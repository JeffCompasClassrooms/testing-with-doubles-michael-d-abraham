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


# fixtures
# still trying to follow the exapmes

@pytest.fixture
def dummy_client():
    return ('127.0.0.1', 80)

@pytest.fixture
def dummy_server():
    return None

# make handler use a tiny write buffer (like the example)
@pytest.fixture(autouse=True)
def patch_wbufsize(mocker):
    mocker.patch.object(SquirrelServerHandler, 'wbufsize', 1)

# stub SquirrelDB.__init__ so we never open sqlite
@pytest.fixture
def mock_db_init(mocker):
    return mocker.patch.object(SquirrelDB, '__init__', return_value=None)

# convenience fixture to mock response methods and assert calls
@pytest.fixture
def mock_response_methods(mocker):
    mock_send_response = mocker.patch.object(SquirrelServerHandler, 'send_response')
    mock_send_header   = mocker.patch.object(SquirrelServerHandler, 'send_header')
    mock_end_headers   = mocker.patch.object(SquirrelServerHandler, 'end_headers')
    return mock_send_response, mock_send_header, mock_end_headers


# tests


def describe_GET():

        def it_lists_all_squirrels_with_200_json(stub_db_ctor, resp_fx, mocker, client, server):
            mock_get = mocker.patch.object(SquirrelDB, "getSquirrels", return_value=["A", "B"])
            req = FakeRequest(mocker.Mock(), "GET", "/squirrels")

            handler = SquirrelServerHandler(req, client, server)

            mock_get.assert_called_once_with()
            send, hdr, end = resp_fx
            send.assert_called_once_with(200)
            hdr.assert_called_once_with("Content-Type", "application/json")
            end.assert_called_once()
            handler.wfile.write.assert_called_once_with(bytes(json.dumps(["A", "B"]), "utf-8"))
