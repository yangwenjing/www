from _mysql import OperationalError
from django import forms
# from django.db import OperationalError
from django.contrib.auth.models import Group
from analysis.core.models import Database, Report
import MySQLdb


class DatabaseForm(forms.ModelForm):

    class Meta:
        model = Database
        fields = ('host', 'port', 'name', 'user', 'password')

        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean(self):
        values = dict(self.cleaned_data.items())
        values.update({
            'passwd': values.get('password', ''),
            'db': values['name']
        })

        del values['name']
        if 'password' in values:
            del values['password']

        try:
            MySQLdb.connect(**values)
        except OperationalError, e:
            raise forms.ValidationError(e)

        return self.cleaned_data


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('name', 'database', 'table')

class DbGroupForm(forms.ModelForm):

    class Meta:
        model = Database
        fields = ('name', 'groups')
        widgets = {'name': forms.HiddenInput()}

    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(),
                                            widget=forms.CheckboxSelectMultiple,
                                            required=False)



