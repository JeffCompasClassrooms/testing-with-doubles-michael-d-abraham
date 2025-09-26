

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

# fixcutes
@pytest.fixture
def dummy_client():
    return ('127.0.0.1', 80)

@pytest.fixture
def dummy_server():
    return None

# small write buffer (I don’t really get why it matters but it works so cool)
@pytest.fixture(autouse=True)
def patch_wbufsize(mocker):
    mocker.patch.object(SquirrelServerHandler, 'wbufsize', 1)

# makes sure that it never opens a real sqlite connection
@pytest.fixture
def mock_db_init(mocker):
    return mocker.patch.object(SquirrelDB, '__init__', return_value=None)

# Took these from the example — these are great
# I read the docs and still only kinda get what’s going on with these
@pytest.fixture
def mock_response_methods(mocker):
    mock_send_response = mocker.patch.object(SquirrelServerHandler, 'send_response')
    mock_send_header   = mocker.patch.object(SquirrelServerHandler, 'send_header')
    mock_end_headers   = mocker.patch.object(SquirrelServerHandler, 'end_headers')
    return mock_send_response, mock_send_header, mock_end_headers


# TESTS
def describe_SquirrelServerHandler():

    # GET /squirrels → handleSquirrelsIndex
    def describe_handleSquirrelsIndex():
        def it_returns_200_and_json_list(mocker, mock_db_init, dummy_client, dummy_server, mock_response_methods):
            # stub DB to return a simple list
            mock_get = mocker.patch.object(SquirrelDB, 'getSquirrels', return_value=['s1'])
            req = FakeRequest(mocker.Mock(), 'GET', '/squirrels')

            handler = SquirrelServerHandler(req, dummy_client, dummy_server)

            # check DB called once, response headers, and correct JSON written
            mock_get.assert_called_once_with()
            send, hdr, end = mock_response_methods
            send.assert_called_once_with(200)
            hdr.assert_called_once_with("Content-Type", "application/json")
            end.assert_called_once()
            handler.wfile.write.assert_called_once_with(bytes(json.dumps(['s1']), 'utf-8'))

    # GET /squirrels/{id} → handleSquirrelsRetrieve
    def describe_handleSquirrelsRetrieve():
        def it_returns_200_and_the_squirrel_when_found(mocker, mock_db_init, dummy_client, dummy_server, mock_response_methods):
            mock_get = mocker.patch.object(SquirrelDB, 'getSquirrel', return_value={'id': '1', 'name': 'Fluffy', 'size': 'large'})
            req = FakeRequest(mocker.Mock(), 'GET', '/squirrels/1')

            handler = SquirrelServerHandler(req, dummy_client, dummy_server)

            # found squirrel → 200, JSON
            mock_get.assert_called_once_with('1')
            send, hdr, end = mock_response_methods
            send.assert_called_once_with(200)
            hdr.assert_called_once_with("Content-Type", "application/json")
            end.assert_called_once()
            handler.wfile.write.assert_called_once_with(bytes(json.dumps({'id': '1', 'name': 'Fluffy', 'size': 'large'}), 'utf-8'))

        def it_calls_handle404_when_id_not_found(mocker, mock_db_init, dummy_client, dummy_server):
            mocker.patch.object(SquirrelDB, 'getSquirrel', return_value=None)
            spy_404 = mocker.patch.object(SquirrelServerHandler, 'handle404')
            req = FakeRequest(mocker.Mock(), 'GET', '/squirrels/999')

            SquirrelServerHandler(req, dummy_client, dummy_server)

            # missing squirrel should trigger handle404
            spy_404.assert_called_once()

    # POST /squirrels → handleSquirrelsCreate
    def describe_handleSquirrelsCreate():
        def it_creates_and_returns_201(mocker, mock_db_init, dummy_client, dummy_server, mock_response_methods):
            # important: server expects form-encoded, not JSON
            req = FakeRequest(mocker.Mock(), 'POST', '/squirrels', body='name=Chippy&size=small')
            mock_create = mocker.patch.object(SquirrelDB, 'createSquirrel', return_value=None)

            SquirrelServerHandler(req, dummy_client, dummy_server)

            mock_create.assert_called_once_with('Chippy', 'small')
            send, hdr, end = mock_response_methods
            send.assert_called_once_with(201)
            end.assert_called_once()
            # create does not write a body
            req._mock_wfile.write.assert_not_called()

        def it_returns_404_if_post_includes_id(mocker, dummy_client, dummy_server, mock_response_methods):
            # router treats POST /squirrels/{id} as 404
            req = FakeRequest(mocker.Mock(), 'POST', '/squirrels/42')

            handler = SquirrelServerHandler(req, dummy_client, dummy_server)

            send, hdr, end = mock_response_methods
            send.assert_called_once_with(404)
            hdr.assert_called_once_with("Content-Type", "text/plain")
            end.assert_called_once()
            handler.wfile.write.assert_called_once_with(b"404 Not Found")

    # PUT /squirrels/{id} → handleSquirrelsUpdate
    def describe_handleSquirrelsUpdate():
        def it_updates_and_returns_204_when_found(mocker, mock_db_init, dummy_client, dummy_server, mock_response_methods):
            mocker.patch.object(SquirrelDB, 'getSquirrel', return_value={'id': '1'})
            mock_update = mocker.patch.object(SquirrelDB, 'updateSquirrel', return_value=None)
            req = FakeRequest(mocker.Mock(), 'PUT', '/squirrels/1', body='name=Nova&size=medium')

            SquirrelServerHandler(req, dummy_client, dummy_server)

            mock_update.assert_called_once_with('1', 'Nova', 'medium')
            send, hdr, end = mock_response_methods
            send.assert_called_once_with(204)
            end.assert_called_once()
            # 204 → no body written
            req._mock_wfile.write.assert_not_called()

        def it_calls_handle404_when_updating_missing(mocker, mock_db_init, dummy_client, dummy_server):
            mocker.patch.object(SquirrelDB, 'getSquirrel', return_value=None)
            spy_update = mocker.patch.object(SquirrelDB, 'updateSquirrel', return_value=None)
            spy_404 = mocker.patch.object(SquirrelServerHandler, 'handle404')
            req = FakeRequest(mocker.Mock(), 'PUT', '/squirrels/404', body='name=X&size=S')

            SquirrelServerHandler(req, dummy_client, dummy_server)

            spy_404.assert_called_once()
            spy_update.assert_not_called()

        def it_returns_404_when_put_has_no_id(mocker, mock_db_init, dummy_client, dummy_server, mock_response_methods):
            # PUT /squirrels (no id) should hit handle404 via do_PUT
            req = FakeRequest(mocker.Mock(), 'PUT', '/squirrels')

            handler = SquirrelServerHandler(req, dummy_client, dummy_server)

            send, hdr, end = mock_response_methods
            send.assert_called_once_with(404)
            hdr.assert_called_once_with("Content-Type", "text/plain")
            end.assert_called_once()
            handler.wfile.write.assert_called_once_with(b"404 Not Found")

    # DELETE /squirrels/{id} → handleSquirrelsDelete
    def describe_handleSquirrelsDelete():
        def it_deletes_and_returns_204_when_found(mocker, mock_db_init, dummy_client, dummy_server, mock_response_methods):
            mocker.patch.object(SquirrelDB, 'getSquirrel', return_value={'id': '2'})
            mock_delete = mocker.patch.object(SquirrelDB, 'deleteSquirrel', return_value=None)
            req = FakeRequest(mocker.Mock(), 'DELETE', '/squirrels/2')

            SquirrelServerHandler(req, dummy_client, dummy_server)

            mock_delete.assert_called_once_with('2')
            send, hdr, end = mock_response_methods
            send.assert_called_once_with(204)
            end.assert_called_once()
            # 204 → no body
            req._mock_wfile.write.assert_not_called()

        def it_calls_handle404_when_deleting_missing(mocker, mock_db_init, dummy_client, dummy_server):
            mocker.patch.object(SquirrelDB, 'getSquirrel', return_value=None)
            spy_delete = mocker.patch.object(SquirrelDB, 'deleteSquirrel', return_value=None)
            spy_404 = mocker.patch.object(SquirrelServerHandler, 'handle404')
            req = FakeRequest(mocker.Mock(), 'DELETE', '/squirrels/123')

            SquirrelServerHandler(req, dummy_client, dummy_server)

            spy_404.assert_called_once()
            spy_delete.assert_not_called()

        def it_returns_404_when_delete_has_no_id(mocker, mock_db_init, dummy_client, dummy_server, mock_response_methods):
            # DELETE /squirrels (no id) should hit handle404 via do_DELETE
            req = FakeRequest(mocker.Mock(), 'DELETE', '/squirrels')

            handler = SquirrelServerHandler(req, dummy_client, dummy_server)

            send, hdr, end = mock_response_methods
            send.assert_called_once_with(404)
            hdr.assert_called_once_with("Content-Type", "text/plain")
            end.assert_called_once()
            handler.wfile.write.assert_called_once_with(b"404 Not Found")

    # Directly test handle404
    def describe_handle404():
        def it_writes_plain_text_404(mocker, mock_db_init, dummy_client, dummy_server, mock_response_methods):
            req = FakeRequest(mocker.Mock(), 'GET', '/anything')
            handler = SquirrelServerHandler(req, dummy_client, dummy_server)

            handler.handle404()

            send, hdr, end = mock_response_methods
            send.assert_called_with(404)
            hdr.assert_called_with("Content-Type", "text/plain")
            end.assert_called()
            handler.wfile.write.assert_called_with(b"404 Not Found")

    # Routing check for unknown resources
    def describe_routing_for_unknown_resource():
        def it_returns_404_for_unknown_collection(mocker, mock_db_init, dummy_client, dummy_server, mock_response_methods):
            # GET /mike should route to handle404 because it doesn’t exist
            req = FakeRequest(mocker.Mock(), 'GET', '/mike')

            handler = SquirrelServerHandler(req, dummy_client, dummy_server)

            send, hdr, end = mock_response_methods
            send.assert_called_once_with(404)
            hdr.assert_called_once_with("Content-Type", "text/plain")
            end.assert_called_once()
            handler.wfile.write.assert_called_once_with(b"404 Not Found")
