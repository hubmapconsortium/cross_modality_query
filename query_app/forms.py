from django import forms
from django.contrib.postgres.forms import SimpleArrayField


class QueryForm(forms.Form):
    output_type = forms.ChoiceField(choices=(('Gene', 'Gene'), ('Cell', 'Cell'), ('Organ', 'Organ')), widget=forms.Select)


class GeneQueryForm(forms.Form):
    input_type = forms.ChoiceField(choices=(('Organ', 'Organ'),), required=True, widget=forms.Select)
    input_set = forms.CharField(max_length=1024, required=True, widget=forms.Textarea)
    logical_operator = forms.ChoiceField(choices=(('and','and'),('or', 'or')), required=True, widget=forms.Select)
    marker = forms.ChoiceField(choices=(('True', 'True'), ('False', 'False')), required=False, widget=forms.Select)
    genomic_modality = forms.ChoiceField(choices=(('rna', 'rna'), ('atac', 'atac')), required=False, widget=forms.Select)


class OrganQueryForm(forms.Form):
    input_type = forms.ChoiceField(choices=(('Cell', 'Cell'), ('Gene', 'Gene')), required=True, widget=forms.Select)
    input_set = forms.CharField(max_length=1024, required=True, widget=forms.Textarea)
    logical_operator = forms.ChoiceField(choices=(('and', 'and'), ('or', 'or')), required=True, widget=forms.Select)
    marker = forms.ChoiceField(choices=(('True', 'True'), ('False', 'False')), widget=forms.Select)
    genomic_modality = forms.ChoiceField(choices=(('rna', 'rna'), ('atac', 'atac')), required=False, widget=forms.Select)


class CellQueryForm(forms.Form):
    input_type = forms.ChoiceField(choices=(('Gene', 'Gene'), ('Protein', 'Protein'), ('Organ', 'Organ')), required=True, widget=forms.Select)
    input_set = forms.CharField(max_length=1024, required=True, widget=forms.Textarea)
    logical_operator = forms.ChoiceField(choices=(('and', 'and'), ('or', 'or')), required=True, widget=forms.Select)
    genomic_modality = forms.ChoiceField(choices=(('rna', 'rna'), ('atac', 'atac')), required=False, widget=forms.Select)
