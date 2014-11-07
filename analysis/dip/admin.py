from django.contrib import admin
from analysis.dip.models import Job, ImportHistory

admin.site.register(Job)
admin.site.register(ImportHistory)
