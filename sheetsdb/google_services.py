import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from . import configs
from .models import SheetsMetaInfo

logger = logging.getLogger(__name__)


def get_spreadsheet(user, spreadsheet_id, range=list(), include_grid_data=False):
    """
    Get spreadsheet

    :param user: User of spreadsheet
    :param spreadsheet_id: Spreadsheet ID to get
    :param range: A1 notation range of data to get. Optional.
    :param include_grid_data: Boolean. Whether to include grid data. Optional.
    :return: Spreadsheet to get, error_status (None indicates no error)
    """
    service = _build_sheets_service(user)
    return _execute_request(
        service.spreadsheets().get(spreadsheetId=spreadsheet_id, ranges=range, includeGridData=include_grid_data))


def create_meta_spreadsheet(user):
    """
    Create and save a new meta spreadsheet for a user

    :param user: User
    :return: Created meta spreadsheet, error_status (None indicates no error)
    """
    service = _build_sheets_service(user)
    meta_spreadsheet, error_status = _execute_request(service.spreadsheets().create(body=configs.META_SPREADSHEET_BODY))
    if error_status is None:
        SheetsMetaInfo(user=user, meta_spreadsheet_id=meta_spreadsheet['spreadsheetId']).save()
    return meta_spreadsheet, error_status


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
