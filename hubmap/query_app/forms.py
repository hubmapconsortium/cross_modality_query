from django import forms


class QueryForm(forms.Form):
    output_type = forms.ChoiceField(choices=(('gene', 'gene'), ('cell', 'cell'), ('organ', 'organ')), widget=forms.Select)


class GeneQueryForm(forms.Form):
    input_type = forms.ChoiceField(choices=(('organ', 'organ'),), required=True, widget=forms.Select)
    input_set = forms.CharField(max_length=1024, required=True, widget=forms.Textarea)
    logical_operator = forms.ChoiceField(choices=(('and', 'and'), ('or', 'or')), required=True, widget=forms.Select)
    marker = forms.ChoiceField(choices=(('True', 'True'), ('False', 'False')), required=False, widget=forms.Select)
    genomic_modality = forms.ChoiceField(choices=(('rna', 'rna'), ('atac', 'atac')), required=False,
                                         widget=forms.Select)


class OrganQueryForm(forms.Form):
    input_type = forms.ChoiceField(choices=(('cell', 'cell'), ('gene', 'gene')), required=True, widget=forms.Select)
    input_set = forms.CharField(max_length=1024, required=True, widget=forms.Textarea)
    logical_operator = forms.ChoiceField(choices=(('and', 'and'), ('or', 'or')), required=True, widget=forms.Select)
    marker = forms.ChoiceField(choices=(('True', 'True'), ('False', 'False')), widget=forms.Select)
    genomic_modality = forms.ChoiceField(choices=(('rna', 'rna'), ('atac', 'atac')), required=False,
                                         widget=forms.Select)


class CellQueryForm(forms.Form):
    input_type = forms.ChoiceField(choices=(('gene', 'gene'), ('protein', 'protein'), ('organ', 'organ')),
                                   required=True, widget=forms.Select)
    input_set = forms.CharField(max_length=1024, required=True, widget=forms.Textarea)
    logical_operator = forms.ChoiceField(choices=(('and', 'and'), ('or', 'or')), required=True, widget=forms.Select)
    genomic_modality = forms.ChoiceField(choices=(('rna', 'rna'), ('atac', 'atac')), required=False,
                                         widget=forms.Select)
