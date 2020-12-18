from django import forms


class QueryForm(forms.Form):
    output_type = forms.ChoiceField(
        choices=(("gene", "gene"), ("cell", "cell"), ("organ", "organ"), ("cluster", "cluster")), widget=forms.Select
    )


class QForm(forms.Form):
    set_key = forms.CharField(max_length=64, required=False, widget=forms.Textarea)
    input_set = forms.CharField(max_length=1024, required=False, widget=forms.Textarea)
    logical_operator = forms.ChoiceField(
        choices=(("and", "and"), ("or", "or")), required=True, widget=forms.Select
    )
    genomic_modality = forms.ChoiceField(
        choices=(("rna", "rna"), ("atac", "atac")), required=False, widget=forms.Select
    )
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
    set_type = forms.ChoiceField(
        choices=(("cell", "cell"),),
        required=True,
        widget=forms.Select,
    )


class GeneQueryForm(QForm):
    input_type = forms.ChoiceField(
        choices=(("organ", "organ"), ("cluster", "cluster")), required=True, widget=forms.Select
    )
    p_value = forms.DecimalField(min_value=0.0, max_value=1.0, required=False)
    set_type = forms.ChoiceField(
        choices=[("gene", "gene")],
        required=True,
        widget=forms.Select,
    )


class OrganQueryForm(QForm):
    input_type = forms.ChoiceField(
        choices=(("gene", "gene"), ("cell", "cell")), required=True, widget=forms.Select
    )
    p_value = forms.DecimalField(min_value=0.0, max_value=1.0, required=False)
    set_type = forms.ChoiceField(
        choices=[("organ", "organ")],
        required=True,
        widget=forms.Select,
    )


class ClusterQueryForm(QForm):
    input_type = forms.ChoiceField(
        choices=(("gene", "gene"),), required=True, widget=forms.Select
    )
    p_value = forms.DecimalField(min_value=0.0, max_value=1.0, required=False)
    set_type = forms.ChoiceField(
        choices=[("cluster", "cluster")],
        required=True,
        widget=forms.Select,
    )

class DatasetQueryForm(QForm):
    input_type = forms.ChoiceField(
        choices=(("cell", "cell"),), required=True, widget=forms.Select
    )
    set_type = forms.ChoiceField(
        choices=[("dataset", "dataset")],
        required=True,
        widget=forms.Select,
    )

class IntersectionForm(forms.Form):
    key_one = forms.CharField(max_length=64)
    key_two = forms.CharField(max_length=64)
    set_type = forms.ChoiceField(
        choices=(("gene", "gene"), ("cell", "cell"), ("organ", "organ"), ("cluster", "cluster")), widget=forms.Select)
    export_format = forms.ChoiceField(
        choices=(("None", "None"), ("csv", "csv"), ("json", "json")),
        required=True,
        widget=forms.Select,
    )


class UnionForm(forms.Form):
    key_one = forms.CharField(max_length=64)
    key_two = forms.CharField(max_length=64)
    set_type = forms.ChoiceField(
        choices=(("gene", "gene"), ("cell", "cell"), ("organ", "organ"), ("cluster", "cluster")), widget=forms.Select)
    export_format = forms.ChoiceField(
        choices=(("None", "None"), ("csv", "csv"), ("json", "json")),
        required=True,
        widget=forms.Select,
    )


class NegationForm(forms.Form):
    key = forms.CharField(max_length=64)
    export_format = forms.ChoiceField(
        choices=(("None", "None"), ("csv", "csv"), ("json", "json")),
        required=True,
        widget=forms.Select,
    )


class EvaluationLandingForm(forms.Form):
    set_type = forms.ChoiceField(
        choices=(("gene", "gene"), ("cell", "cell"), ("organ", "organ"), ("cluster", "cluster")), widget=forms.Select)


class ListLandingForm(forms.Form):
    set_type = forms.ChoiceField(
        choices=(("gene", "gene"), ("cell", "cell"), ("organ", "organ"), ("cluster", "cluster")), widget=forms.Select)


class EvaluationForm(forms.Form):
    key = forms.CharField(max_length=64)
    values_included = forms.CharField(max_length=256, required=False)
    sort_by = forms.CharField(max_length=32, required=False)
    export_format = forms.ChoiceField(
        choices=(("None", "None"), ("csv", "csv"), ("json", "json")),
        required=True,
        widget=forms.Select,
    )
    limit = forms.IntegerField()
    values_type = forms.ChoiceField(choices=(("gene", "gene"), ("protein", "protein"), ("organ", "organ"), ("cluster", "cluster")))

class ListForm(forms.Form):
    key = forms.CharField(max_length=64)
    set_type = forms.ChoiceField(
        choices=(("gene", "gene"), ("cell", "cell"), ("organ", "organ"), ("cluster", "cluster"), ("dataset", "dataset")), widget=forms.Select)
    export_format = forms.ChoiceField(
        choices=(("None", "None"), ("csv", "csv"), ("json", "json")),
        required=True,
        widget=forms.Select,
    )
    limit = forms.IntegerField()


class CountForm(forms.Form):
    key = forms.CharField(max_length=32)
    set_type = forms.ChoiceField(
        choices=(("gene", "gene"), ("cell", "cell"), ("organ", "organ"), ("cluster", "cluster"), ("dataset", "dataset")), widget=forms.Select)
    export_format = forms.ChoiceField(
        choices=(("None", "None"), ("csv", "csv"), ("json", "json")),
        required=True,
        widget=forms.Select,
    )
