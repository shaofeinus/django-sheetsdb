from django.contrib.auth.models import User
from django.db import models
from django.db.models import OneToOneField, CharField
from django.forms import ModelForm


# Models
class SheetsMetaInfo(models.Model):
    user = OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    meta_spreadsheet_id = CharField(max_length=64)


# Forms
class SheetsMetaInfoForm(ModelForm):
    class Meta:
        model = SheetsMetaInfo
        fields = ['meta_spreadsheet_id', ]
