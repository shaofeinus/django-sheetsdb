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
