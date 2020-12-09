from django import forms


class QueryForm(forms.Form):
    output_type = forms.ChoiceField(
        choices=(("gene", "gene"), ("cell", "cell"), ("organ", "organ"), ("cluster", "cluster")), widget=forms.Select
    )


class QForm(forms.Form):
    input_set = forms.CharField(max_length=1024, required=True, widget=forms.Textarea)
    logical_operator = forms.ChoiceField(
        choices=(("and", "and"), ("or", "or")), required=True, widget=forms.Select
    )
    genomic_modality = forms.ChoiceField(
        choices=(("rna", "rna"), ("atac", "atac")), required=False, widget=forms.Select
    )
    limit = forms.IntegerField(max_value=1000, min_value=0, required=False)
    export_format = forms.ChoiceField(
        choices=(("None", "None"), ("csv", "csv"), ("json", "json")),
        required=True,
        widget=forms.Select,
    )


class CellForm(QForm):
    input_type = forms.ChoiceField(
        choices=(("gene", "gene"), ("protein", "protein"), ("organ", "organ"), ("dataset", "dataset")),
        required=True,
        widget=forms.Select,
    )


class GeneQueryForm(QForm):
    input_type = forms.ChoiceField(
        choices=(("organ", "organ"), ("cluster", "cluster")), required=True, widget=forms.Select
    )
    p_value = forms.DecimalField(min_value=0.0, max_value=1.0, required=False)


class OrganQueryForm(QForm):
    input_type = forms.ChoiceField(
        choices=(("gene", "gene"), ("cell", "cell")), required=True, widget=forms.Select
    )
    p_value = forms.DecimalField(min_value=0.0, max_value=1.0, required=False)


class ClusterQueryForm(QForm):
    input_type = forms.ChoiceField(
        choices=(("gene", "gene"),), required=True, widget=forms.Select
    )
    p_value = forms.DecimalField(min_value=0.0, max_value=1.0, required=False)
