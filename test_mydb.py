import os
import pytest
from mydb import MyDB


todo = pytest.mark.skip(reason='still need to do')

def describe_MyDB():

    # Safety check: nothing should actually write a file during this test session
    @pytest.fixture(autouse=True, scope="session")
    def verify_filesystem_is_not_touched():
        yield
        assert not os.path.isfile("mydatabase.db")
    
    # from example to work throuhg
    def describe_init():

        def it_assigns_fname_attribute(mocker):
            # Stub os.path.isfile so __init__ won’t try to create a file
            mocker.patch("os.path.isfile", return_value=True)
            db = MyDB("mydatabase.db")
            assert db.fname == "mydatabase.db"

        def it_creates_empty_database_if_it_does_not_exist(mocker):
            # Set up stubs and mocks first
            # This foces the file does not exist branch
            mock_isfile = mocker.patch("os.path.isfile", return_value=False)
            # Fake file hand (so nothing is written)
            mock_open = mocker.patch("builtins.open", mocker.mock_open())
            mock_dump = mocker.patch("pickle.dump")

            # the action
            MyDB("mydatabase.db")

            # This is the asserts to see what happened
            # These are built in function for mocker
            # see if mydatabase.db was called examply once
            mock_isfile.assert_called_once_with("mydatabase.db")
            mock_open.assert_called_once_with("mydatabase.db", "wb")
            mock_dump.assert_called_once_with([], mock_open.return_value)

        def it_does_not_create_database_if_it_already_exists(mocker):
            # Arrange: force the "file exists" branch
            mock_isfile = mocker.patch("os.path.isfile", return_value=True)
            mock_open = mocker.patch("builtins.open", mocker.mock_open())
            mock_dump = mocker.patch("pickle.dump")

            # Act
            MyDB("mydatabase.db")

            # Assert: no writes if the file already exists
            mock_isfile.assert_called_once_with("mydatabase.db")
            mock_open.assert_not_called()
            mock_dump.assert_not_called()

