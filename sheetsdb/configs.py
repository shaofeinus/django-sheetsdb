from django.conf import settings

META_SPREADSHEET_TITLE = 'sheetsdb/meta'

META_SPREADSHEET_BODY = {
    'properties': {
        'title': META_SPREADSHEET_TITLE,
        'locale': 'en',
        'autoRecalc': 'ON_CHANGE',
        'timeZone': 'UTC',
    },
    'sheets': [{
        'properties': {
            'sheetId': 0,
            'title': META_SPREADSHEET_TITLE,
            'index': 0,
        }
    }]
}

UPDATE_META_SPREADSHEET_ID_TEMPLATE = getattr(
    settings, 'SHEETSDB_UPDATE_META_SPREADSHEET_ID_TEMPLATE', 'sheetsdb/update_meta_spreadsheet_id.html')

META_SPREADSHEET_COL_DEFS = [
    {
        'name': 'database_name',
        'type': 'string',
    },
    {
        'name': 'table_name',
        'type': 'string',
    },
    {
        'name': 'spreadsheet_id',
        'type': 'string',
    },
    {
        'name': 'col_defs',
        'type': 'json',
    },
]

META_DATABASE_NAME = 'sheetsdb'

META_TABLE_NAME = 'meta'
