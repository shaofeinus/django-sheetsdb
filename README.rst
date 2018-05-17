========
Sheetsdb
========

Sheetsdb allows Google Sheets to be used as a database in Django applications.

Pre-requisite
-------------

The `googleauth` library must also be included in the same application.

To install `googleauth`, run ``pip install django-google-auth``.
Follow the README file in `googleauth` package to set up the library.

Configurations
--------------

Configurations need to be set for the following files in your project.

settings.py
^^^^^^^^^^^

**Required:**

1. Add `sheetsdb` to `INSTALLED_APPS`::

    INSTALLED_APPS = [
        ...
        'sheetsdb',
    ]

2. Add ''https://www.googleapis.com/auth/spreadsheets'' to 'GOOGLE_API_SCOPES' to have read/write access Google Sheets::
   
    GOOGLE_API_SCOPES = [
        ''https://www.googleapis.com/auth/spreadsheets'',
        ...
    ]
   
   This list can be extended by other google API access applications.

**Optional:**

1. Set default sheetsdb index template as `SHEETSDB_INDEX_TEMPLATE`::

    SHEETSDB_INDEX_TEMPLATE = 'app/sheetsdb_index.html'

   If this template is not set, a default page will be use (sheetsdb/index.html).

   The follow context variables will be available for the template:

   * `next`: The url to redirect to after update of spreadsheet ID succeeds
   * `reason`: Reason for need to update spreadsheet ID
   * `meta_spreadsheet_title`: The title of the meta spreadsheet
   * `form`: Form entity for update of spreadsheet ID

2. Set default update meta spreadsheet ID template as `SHEETSDB_UPDATE_META_SPREADSHEET_ID_TEMPLATE`::

    SHEETSDB_UPDATE_META_SPREADSHEET_ID_TEMPLATE = 'app/update_meta_spreadsheet_id.html'

   If this template is not set, a default page will be use (sheetsdb/update_meta_spreadsheet_id.html).

   The follow context variables will be available for the template:

   * `meta_spreadsheet_id`: The ID of the meta spreadsheet
   * `num_tables`: Number of database tables
   * `table_list`: List of `table` representing the database tables. Each `table` contains:
       * `name`: Name of table
       * `num_rows`: Number of rows in table
       * `last_modified_datetime`: Last modified date time of table
       * `spreadsheet_id`: ID of spreadsheet containing the table data
       * `spreadsheet_link`: Link to spreadsheet containing the table data


urls.py
^^^^^^^

Add googleauth URLconf to `urlpatterns`::

    urlpatterns = [
        ...
        path('sheetsdb/', include('sheetsdb.urls')),
    ]



Sheetsdb SDK
------------

All database functions can be executed using the `SheetsdbSDK` object.

To access the `SheetsdbSDK` in a view, simply add the `@require_sheetsdb_sdk` decorator to the view function.
The `SheetsdbSDK` can then be accessed from the `sheetsdb_sdk` argument in the view function::

    from django.contrib.auth.decorators import login_required
    from sheetsdb.decorators import require_sheetsdb_sdk
    ...

    @login_required
    @require_sheetsdb_sdk
    def my_view(request, sheetsdb_sdk):
        ...
        sheetsdb_sdk.select(...)
        ...

Note that the django `@login_required` decorator needs to be placed BEFORE the `@require_sheetsdb_sdk` decorator
as the `@require_sheetsdb_sdk` require information of the logged in user to create the `SheetsdbSDK` object.

The functions provided by `SheetsdbSDK` are documented below.



Select
^^^^^^

*TODO*

Insert/Update
^^^^^^^^^^^^^

*TODO*


Delete
^^^^^^

*TODO*