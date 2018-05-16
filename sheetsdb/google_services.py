import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from . import configs
from .models import SheetsMetaInfo

logger = logging.getLogger(__name__)


def get_bounded_range_values(user, spreadsheet_id,
                             start_row_index, start_col_index, end_row_index, end_col_index):
    """
    Get values in a bounded range in a spreadsheet.

    :type user: django.contrib.auth.models.User
    :param user: User of spreadsheet to get values from
    :type spreadsheet_id: str
    :param spreadsheet_id: Spreadsheet ID of spreadsheet to get values from
    :type start_row_index: int
    :param start_row_index: 0-based index of starting (inclusive) row of range
    :type start_col_index: int
    :param start_col_index: 0-based index of starting (inclusive) column of range
    :type end_row_index: int
    :param end_row_index: 0-based index of ending (inclusive) row of range
    :type end_col_index: int
    :param end_col_index: 0-based index of ending (inclusive) column of range
    :rtype: Google `ValueRange` resource, int
    :return: Queried data, error_status (None indicates no error)
    """
    if start_row_index < 0 or start_col_index < 0 or end_row_index < 0 or end_col_index < 0:
        raise ValueError('Negative index')
    service = _build_sheets_service(user)
    start_cell = _convert_to_a1(start_row_index, start_col_index)
    end_cell = _convert_to_a1(end_row_index, end_col_index)
    return _execute_request(
        service.spreadsheets().values().get(spreadsheet_id=spreadsheet_id, range="{}:{}".format(start_cell, end_cell)))


def get_columns_values(user, spreadsheet_id, start_col_index, end_col_index):
    """
    Get all available values in a bounded column range in a spreadsheet.

    :type user: django.contrib.auth.models.User
    :param user: User of spreadsheet to get values from
    :type spreadsheet_id: str
    :param spreadsheet_id: Spreadsheet ID of spreadsheet to get values from
    :type start_col_index: int
    :param start_col_index: 0-based index of starting (inclusive) column
    :type end_col_index: int
    :param end_col_index: 0-based index of ending (inclusive) column
    :rtype: Google `ValueRange` resource, int
    :return: Queried data, error_status (None indicates no error)
    """
    if start_col_index == -1 or end_col_index == -1:
        raise ValueError('Negative index')
    service = _build_sheets_service(user)
    start_cell = _convert_to_a1(col_index=start_col_index)
    end_cell = _convert_to_a1(col_index=end_col_index)
    return _execute_request(
        service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range="{}:{}".format(start_cell, end_cell)))


def get_spreadsheet(user, spreadsheet_id):
    """
    Get spreadsheet

    :type user: django.contrib.auth.models.User
    :param user: User of spreadsheet
    :type spreadsheet_id: str
    :param spreadsheet_id: Spreadsheet ID to get
    :rtype: Google `Spreadsheet` resource, int
    :return: Spread sheet to get, error_status (None indicates no error)
    """
    service = _build_sheets_service(user)
    return _execute_request(
        service.spreadsheets().get(spreadsheetId=spreadsheet_id, includeGridData=False))


def create_meta_spreadsheet(user):
    """
    Create and save a new meta spreadsheet for a user

    :param user: User
    :rtype: Google `Spreadsheet` resource, int
    :return: Created meta spreadsheet, error_status (None indicates no error)
    """
    service = _build_sheets_service(user)
    meta_spreadsheet, error_status = _execute_request(service.spreadsheets().create(body=configs.META_SPREADSHEET_BODY))
    if error_status is None:
        SheetsMetaInfo(user=user, meta_spreadsheet_id=meta_spreadsheet['spreadsheetId']).save()
    return meta_spreadsheet, error_status


def _convert_to_a1(row_index=None, col_index=None):
    """
    Convert a row and column index pair to A1 notation. At least 1 of row or column index is required.

    :type row_index: int
    :param row_index: 0-based row index
    :type col_index: int
    :param col_index: 0-based column index
    :rtype: str
    :return: A1 notation of row and column index pair
    """
    if row_index is None and col_index is None:
        raise ValueError('Both row and column indexes are None')
    if (row_index is not None and row_index) < 0 or (col_index is not None and col_index < 0):
        raise ValueError('Negative index')
    if col_index is not None and col_index > 255:
        raise ValueError('Column index {} exceeds limits')

    # Row
    row_component = str(row_index + 1) if row_index is not None else ''

    # Column
    col_component = ''
    if col_index is not None:
        column_index_mapping = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                                'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        num_letters = len(column_index_mapping)
        first_letter_index = col_index // num_letters - 1
        second_letter_index = col_index % num_letters
        if first_letter_index >= 0:
            col_component = column_index_mapping[first_letter_index] + column_index_mapping[second_letter_index]
        else:
            col_component = column_index_mapping[second_letter_index]

    return '{}{}'.format(col_component, row_component)


def _execute_request(api_request):
    """
    Execute an API request

    :param api_request: API request
    :return: response, error_status (None indicates no error)
    """
    response = None
    error_status = None
    try:
        response = api_request.execute()
    except HttpError as http_error:
        logger.exception('Error when executing request')
        error_status = http_error.resp.status
    return response, error_status


def _build_sheets_service(user):
    """
    Build a service to call Sheets API

    :param user: User to build service for
    :return: service object
    """
    return build('sheets', 'v4', credentials=user.googlecreds.credentials)


def _build_drive_service(user):
    """
    Build a service to call Drive API

    :param user: User to build service for
    :return: service object
    """
    return build('drive', 'v3', credentials=user.googlecreds.credentials)
