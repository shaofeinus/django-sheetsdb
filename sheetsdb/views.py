import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from . import configs
from .configs import UPDATE_META_SPREADSHEET_ID_TEMPLATE
from .decorators import require_sheetsdb_sdk
from .models import SheetsMetaInfoForm

logger = logging.getLogger(__name__)


@login_required
@require_sheetsdb_sdk
def index(request, sheetsdb_sdk):
    sheets_link = 'https://docs.google.com/spreadsheets/d/{}/'
    meta_spreadsheet_id = sheetsdb_sdk.get_meta_spreadsheet_id()
    tables = sheetsdb_sdk.get_all_tables_info()
    for table in tables:
        table['spreadsheet_link'] = sheets_link.format(table['spreadsheet_id'])
    return render(request, 'sheetsdb/index.html', {
        'meta_spreadsheet_id': meta_spreadsheet_id,
        'meta_spreadsheet_link': sheets_link.format(meta_spreadsheet_id),
        'num_tables': len(tables),
        'tables': tables
    })


@login_required
@require_http_methods(['GET', 'POST'])
def update_meta_spreadsheet_id(request):
    if request.method == 'GET':
        return render(request, UPDATE_META_SPREADSHEET_ID_TEMPLATE,
                      {
                          'next': request.GET.get('next'),
                          'reason': request.GET.get('reason'),
                          'meta_spreadsheet_title': configs.META_SPREADSHEET_TITLE,
                          'form': SheetsMetaInfoForm()
                      })
    elif request.method == 'POST':
        form = SheetsMetaInfoForm(request.POST)
        sheets_meta_info = form.save(commit=False)
        sheets_meta_info.user = request.user
        sheets_meta_info.save()
        next_url = request.GET.get('next')
        if next_url is not None:
            return redirect(next_url)
        else:
            return redirect(reverse('sheetsdb-index'))
