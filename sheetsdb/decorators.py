import logging

from django.shortcuts import redirect
from django.urls import reverse

from . import configs
from . import google_services
from .sdk import SheetsdbSDK

logger = logging.getLogger(__name__)


def require_meta_spreadsheet(view_func):
    """
    Gets the meta spreadsheet of user and set it as the `meta_spreadsheet` argument of view.
    If there is an error when retrieving meta spreadsheet, redirect to the `sheetsdb-update-meta-spreadsheet-id` view,
    with query string:
        * `next` indicating the redirect URL when update is successful
        * `reason` indicating reason of error

    Only for advanced usage
    """

    def redirect_to_update_meta_spreadsheet_id(request, reason):
        return redirect('{}?next={}&reason={}'.format(
            reverse('sheetsdb-update-meta-spreadsheet-id'),
            request.get_full_path(),
            reason))

    def view_func_wrapper(request, **kwargs):
        user = request.user

        if not hasattr(user, 'sheetsmetainfo'):
            # No meta spreadsheet information found, create one
            logger.info('Meta spreadsheet not found for user {} in DB. Creating one...', user.email)
            meta_spreadsheet, error_status = google_services.create_meta_spreadsheet(user)
            if error_status is not None:
                reason = 'Error status {} when creating meta spreadsheet'.format(error_status)
                logger.error(reason)
                return redirect_to_update_meta_spreadsheet_id(request, reason)
            else:
                logger.info('Meta spreadsheet {} created'.format(meta_spreadsheet['spreadsheetId']))

        else:
            # Get meta spreadsheet info
            meta_spreadsheet_id = user.sheetsmetainfo.meta_spreadsheet_id
            meta_spreadsheet, error_status = google_services.get_spreadsheet(user, meta_spreadsheet_id)

            # Sheets API errors
            if error_status == 404:
                reason = 'Meta spreadsheet {} not found'.format(meta_spreadsheet_id)
                logger.error(reason)
                return redirect_to_update_meta_spreadsheet_id(request, reason)
            elif error_status is not None:
                reason = 'Error when getting meta spreadsheet'
                logger.error(reason)
                return redirect_to_update_meta_spreadsheet_id(request, reason)

            # Meta spreadsheet errors
            meta_spreadsheet_title = meta_spreadsheet['properties']['title']
            if not meta_spreadsheet_title == configs.META_SPREADSHEET_TITLE:
                reason = 'Meta spreadsheet {} title "{}" does not matched required title "{}"'.format(
                    meta_spreadsheet_id, meta_spreadsheet_title, configs.META_SPREADSHEET_TITLE)
                logger.error(reason)
                return redirect_to_update_meta_spreadsheet_id(request, reason)

        return view_func(request, meta_spreadsheet=meta_spreadsheet, **kwargs)

    return view_func_wrapper


def require_sheetsdb_sdk(view_func):
    """
    Get a `SheetsdbSDK` object for user and set it as the `sheetsdb_sdk` argument of view.
    """

    def view_func_wrapper(request, meta_spreadsheet, **kwargs):
        return view_func(request, sheetsdb_sdk=SheetsdbSDK(user=request.user, meta_spreadsheet=meta_spreadsheet),
                         **kwargs)

    return require_meta_spreadsheet(view_func_wrapper)
