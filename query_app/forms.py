from django import forms
from django.contrib.postgres.forms import SimpleArrayField


class QueryForm(forms.Form):
    output_type = forms.ChoiceField(choices=(('Gene', None), ('Cell', None), ('Organ', None)))


class GeneQueryForm(forms.Form):
    input_type = forms.ChoiceField(choices=(('Organ', None)))
    input_set = SimpleArrayField(base_field=forms.CharField())
    logical_operator = forms.ChoiceField(choices=(('and', None), ('or', None)))
    marker = forms.BooleanField()


class OrganQueryForm(forms.Form):
    input_type = forms.ChoiceField(choices=(('Cell', None), ('Gene', None)))
    input_set = SimpleArrayField(base_field=forms.CharField())
    logical_operator = forms.ChoiceField(choices=(('and', None), ('or', None)))
    marker = forms.BooleanField


class CellQueryForm(forms.Form):
    input_type = forms.ChoiceField(choices=(('Gene', None), ('Protein', None), ('Organ', None)))
    input_set = SimpleArrayField(base_field=forms.CharField())
    logical_operator = forms.ChoiceField(choices=(('and', None), ('or', None)))
