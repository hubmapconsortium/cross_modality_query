import django_tables2 as tables

from . import models


class CellTable(tables.Table):
    cell_id = tables.Column(accessor='cell_id')
    modality = tables.Column(accessor='modality')
    protein_mean = tables.Column(accessor='protein_mean')
    protein_total = tables.Column(accessor='protein_total')
    protein_covar = tables.Column(accessor='protein_covar')

    class Meta:
        model = models.Cell


class GeneTable(tables.Table):
    gene_symbol = tables.Column(accessor='gene_symbol')
    go_terms = tables.Column(accessor='go_terms')

    class Meta:
        model = models.Gene


class OrganTable(tables.Table):
    organ_name = tables.Column(accessor='group_id')

    class Meta:
        model = models.CellGrouping
