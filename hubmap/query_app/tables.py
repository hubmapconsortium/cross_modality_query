import django_tables2 as tables

from . import models


class CellTable(tables.Table):
    cell_id = tables.Column(accessor="cell_id")
    organ = tables.Column(accessor="organ")
    dataset = tables.Column(accessor="dataset")
    modality = tables.Column(accessor="modality")
    protein_mean = tables.Column(accessor="protein_mean")
    protein_total = tables.Column(accessor="protein_total")
    protein_covar = tables.Column(accessor="protein_covar")

    class Meta:
        model = models.Cell


class GeneTable(tables.Table):
    gene_symbol = tables.Column(accessor="gene_symbol")
    go_terms = tables.Column(accessor="go_terms")

    class Meta:
        model = models.Gene


class OrganTable(tables.Table):
    grouping_name = tables.Column(accessor="grouping_name")

    class Meta:
        model = models.Organ
        fields = ["grouping_name"]


class ProteinTable(tables.Table):
    protein_id = tables.Column(accessor="protein_id")
    go_terms = tables.Column(accessor="go_terms")

    class Meta:
        model = models.Protein


class ClusterTable(tables.Table):
    cluster_method = tables.Column(accessor="cluster_method")
    cluster_data = tables.Column(accessor="cluster_data")
    grouping_name = tables.Column(accessor="grouping_name")
    dataset = tables.Column(accessor="dataset")

    class Meta:
        model = models.Cluster


class DatasetTable(tables.Table):
    uuid = tables.Column(accessor="uuid")

    class Meta:
        model = models.Dataset


class CellAndValuesTable(tables.Table):
    class Meta:
        model = models.CellAndValues
        fields = ["cell_id", "dataset", "modality", "organ", "values"]
        template_name = "django_tables2/bootstrap4.html"


class GeneAndValuesTable(tables.Table):
    class Meta:
        model = models.GeneAndValues
        fields = ["gene_symbol", "go_terms", "values"]
        template_name = "django_tables2/bootstrap4.html"


class OrganAndValuesTable(tables.Table):
    class Meta:
        model = models.OrganAndValues
        fields = ["grouping_name", "values"]
        template_name = "django_tables2/bootstrap4.html"


class ClusterAndValuesTable(tables.Table):
    dataset = tables.Column(accessor="dataset")

    class Meta:
        model = models.ClusterAndValues
        fields = ["grouping_name", "dataset", "values"]
        template_name = "django_tables2/bootstrap4.html"


class QuerySetTable(tables.Table):
    class Meta:
        model = models.Cell
        template_name = "django_tables2/bootstrap4.html"


class QuerySetCountTable(tables.Table):
    class Meta:
        model = models.Cell
        template_name = "django_tables2/bootstrap4.html"
