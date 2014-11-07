#coding: utf-8
from django import forms
from analysis.collection.models import Collection, Report, Link


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ('creator', 'name', 'group')

    def clean(self):
        cleaned_data = super(CollectionForm, self).clean()

        name = cleaned_data.get('name')
        creator = cleaned_data.get('creator')

        if Collection.objects.filter(creator=creator, name=name).exists():
            raise forms.ValidationError("已经存在此集合！")

        if name.lower() == 'dashboard':
            raise forms.ValidationError("不能使用Dashboard为集合名称")

        return cleaned_data


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('name', 'collection', 'url', 'creator')

    url = forms.URLField()

class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ('name', 'url', 'group')

        widgets = {
            'group': forms.Select()
        }
    url = forms.URLField()
