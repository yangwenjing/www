# coding: utf8
from django import forms

from analysis.aggregate.models import AggregateJob


class AggregateJobForm(forms.ModelForm):
    class Meta:

        model = AggregateJob
        fields = ('database', 'table', 'datetime_fields', 'aggregate_fields', 'sum_fields', 'remain_days')
        widgets = {
            'table': forms.Select(),
            'aggregate_fields': forms.TextInput(),
            'sum_fields': forms.TextInput()
        }


    def clean(self):
        cleaned_data = self.cleaned_data

        print(cleaned_data)
        db = cleaned_data.get('database')

        # if not Database.objects.filter(id=dbid):
        # raise forms.ValidationError("数据库错误！")
        #
        # db = Database.objects.get(id=dbid)
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute('show tables;')

        table = cleaned_data.get('table')
        if not (table,) in cursor.fetchall():
            raise forms.ValidationError("表名错误！")

        cursor.execute('show columns from `%s`' % table)
        fields_name = [row[0] for row in cursor]
        fields_type = [row[1] for row in cursor]

        # datetime_fields
        dt_fields_list = cleaned_data.get('datetime_fields').split(',')
        if len(dt_fields_list) > 2:
            raise forms.ValidationError("最多只能压缩两个时间字段")

        for dt_field in dt_fields_list:
            try:
                i = fields_name.index(dt_field)
                _type = fields_type[i]

                # 类型是否合理，未实现
                fields_name.pop(i)
                fields_type.pop(i)

            except ValueError, e:
                raise forms.ValidationError("时间字段名称错误: %s.可能由于该字段已使用。" % e)

        # aggregate_fields
        aggregate_field = cleaned_data.get('aggregate_fields').replace(" ", "")
        if aggregate_field != "":
            aggregate_fields_list = aggregate_field.split(',')

            for field in aggregate_fields_list:
                try:
                    i = fields_name.index(field)
                    _type = fields_type[i]

                    # 类型是否合理，未实现
                    fields_name.pop(i)
                    fields_type.pop(i)

                except ValueError, e:
                    raise forms.ValidationError("聚合维度名称错误: %s.可能由于该字段已使用。" % e)

        sum_field_list = cleaned_data.get('sum_fields').split(',')
        for field in sum_field_list:
            try:
                i = fields_name.index(field)
                _type = fields_type[i]

                #类型是否合理，未实现
                fields_name.pop(i)
                fields_type.pop(i)

            except ValueError, e:
                raise forms.ValidationError("聚合字段名称错误: %s. 可能由于该字段已使用。" % e)

        return cleaned_data













