from django import forms
from django.contrib.postgres.forms import SimpleArrayField

class QueryForm(forms.Form):
    output_type = forms.ChoiceField(choices=(('Gene', None), ('Cell', None), ('Organ', None)))

class GeneForm(forms.Form):
    hugo_symbols = SimpleArrayField(forms.CharField(max_length=100))

class OrganForm(forms.Form):
    organs = SimpleArrayField(forms.CharField(max_length=100))

class CellForm(forms.Form):
    cell_ids = SimpleArrayField(forms.CharField(max_length=100))

class ProteinForm(forms.Form):
    protein_id = SimpleArrayField(forms.CharField(max_length=100))
