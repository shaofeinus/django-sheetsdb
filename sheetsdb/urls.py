from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='sheetsdb-index'),
    path('update-meta-spreadsheet-id/', views.update_meta_spreadsheet_id, name='sheetsdb-update-meta-spreadsheet-id'),
]
