from django.contrib import admin

# Register your models here.
from analysis.collection.models import Collection, Report

admin.site.register(Collection)
admin.site.register(Report)