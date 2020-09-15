from django import forms
from django.contrib.postgres.forms import SimpleArrayField


class QueryForm(forms.Form):
    output_type = forms.ChoiceField(choices=(('Gene', None), ('Cell', None), ('Organ', None)))


class GeneQueryForm(forms.Form):
    input_type = forms.ChoiceField(choices=(('Organ', None)), required=True)
    input_set = SimpleArrayField(base_field=forms.CharField(max_length=1024), required=True)
    logical_operator = forms.ChoiceField(choices=(('and', None), ('or', None)), required=True)
    marker = forms.BooleanField(required=True)


class OrganQueryForm(forms.Form):
    input_type = forms.ChoiceField(choices=(('Cell', None), ('Gene', None)), required=True)
    input_set = SimpleArrayField(base_field=forms.CharField(max_length=1024), required=True)
    logical_operator = forms.ChoiceField(choices=(('and', None), ('or', None)), required=True)
    marker = forms.BooleanField(required=True)


class CellQueryForm(forms.Form):
    input_type = forms.ChoiceField(choices=(('Gene', None), ('Protein', None), ('Organ', None)), required=True)
    input_set = SimpleArrayField(base_field=forms.CharField(max_length=1024), required=True)
    logical_operator = forms.ChoiceField(choices=(('and', None), ('or', None)), required=True)
