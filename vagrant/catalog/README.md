# Catalog
Application allowing users to view, add, edit, and delete items in a database,
where items are grouped together by category. An item can only be modified or
deleted by the user that created it.

## To run the application:
 - Run the command `python database_setup.py` to create the database
 - Run `python application.py` to start the server
 - The homepage is located at http://localhost:8000
 - A Google account must be used to test creating and modifying items
 - The public JSON API can get seen with a GET request to
 http://localhost:8000/catalog/JSON
