from django import forms
from analysis.dip.models import Job


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ('database', 'table', 'dip_id', 'dip_alias', 'interval')

        widgets = {
            'table': forms.Select()
        }
