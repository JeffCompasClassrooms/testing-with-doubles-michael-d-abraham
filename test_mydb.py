import os
import pytest
from mydb import MyDB


todo = pytest.mark.skip(reason='still need to do')

def describe_MyDB():

    # Safety check: nothing should actually write a file during this test session
    # autoTrue means it will run automatically for every matching scope session kinda cool

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
            # sees that the open file is called once in bytes
            mock_open.assert_called_once_with("mydatabase.db", "wb")
            # This see that mock_dump was called exaactly once and creates []
            mock_dump.assert_called_once_with([], mock_open.return_value)

        def it_does_not_create_database_if_it_already_exists(mocker):
            # Arrange: force the "file exists" branch
            mock_isfile = mocker.patch("os.path.isfile", return_value=True)
            # swaps the python open for the mock open isntad
            mock_open = mocker.patch("builtins.open", mocker.mock_open())
            # Any where pickle dump would be used we use mocker instead
            mock_dump = mocker.patch("pickle.dump")

            # Act
            MyDB("mydatabase.db")

            # Assert: no writes if the file already exists
            # Checks to see if your stubbed functions were called during the test
            mock_isfile.assert_called_once_with("mydatabase.db")
            mock_open.assert_not_called()
            mock_dump.assert_not_called()


    def describe_loadStrings():

        def it_returns_list_from_file(mocker):
            # use the mocker open instead
            mocker.patch("builtins.open", mocker.mock_open())
            # fake pickle.oad so it just retunrs mike, gaot
            mock_load = mocker.patch("pickle.load", return_value=["Mike", "Goat"])
            # when it checks to see if there is a file say yes there is one
            mocker.patch("os.path.isfile", return_value=True)

            # call the homie
            db = MyDB("mydatabase.db")
            result = db.loadStrings()

            # and finally check to see if its correct
            assert result == ["Mike", "Goat"]
            # and it should of only ran exactly one time
            mock_load.assert_called_once()

    def describe_saveStrings():

        def it_writes_array_to_file(mocker):
            # Fake the opening
            mock_open = mocker.patch("builtins.open", mocker.mock_open())

            # fake the dump
            mock_dump = mocker.patch("pickle.dump")

            # show that arr exsits or the file
            mocker.patch("os.path.isfile", return_value=True)

            # call the bro
            db = MyDB("mydatabase.db")
            db.saveStrings(["Mike","Going","Places"])

            # check to see if it worked
            mock_open.assert_called_once_with("mydatabase.db", "wb")
            mock_dump.assert_called_once_with(["Mike","Going","Places"], mock_open.return_value)

    def describe_saveString():

        def it_adds_one_string(mocker):
            # repalce the function with mocker and have "Mike, Is" be passed in as if it was the db
            mock_loadStrings = mocker.patch.object(MyDB, "loadStrings", return_value=["Mike", "Is"])
            #mock the savestring function for my mine that doesn't do anything
            mock_saveStrings = mocker.patch.object(MyDB, "saveStrings")
            # Show that there is a file even tho theres not

            mocker.patch("os.path.isfile", return_value=True)

            # run it

            db = MyDB("mydatabase.db")
            db.saveString("HIM")

            # loadstrings is called only once
            mock_loadStrings.assert_called_once()
            # that saveStrings is called only once and with the added HIM
            mock_saveStrings.assert_called_once_with(["Mike", "Is", "HIM"])



            
