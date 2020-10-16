import django_tables2 as tables

from . import models


class CellTable(tables.Table):
    cell_id = tables.Column(accessor='cell_id')
    organ = tables.Column(accessor='organ')
    dataset = tables.Column(accessor='dataset')
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
    organ_name = tables.Column(accessor='organ_name')

    class Meta:
        model = models.Organ

class ProteinTable(tables.Table):
    protein_id = tables.Column(accessor='protein_id')
    go_terms = tables.Column(accessor='go_terms')

    class Meta:
        model = models.Protein

class OrganPValTable(tables.Table):
    organ_name = tables.Column(accessor='organ_name')
    value = tables.Column(accessor='value')

    class Meta:
        model = models.PVal

class GenePValTable(tables.Table):
    organ_name = tables.Column(accessor='organ_name')
    value = tables.Column(accessor='value')

    class Meta:
        model = models.PVal

class CellQuantTable(tables.Table):
    value = tables.Column(accessor='value')
    cell_id = tables.Column(accessor='cell.cell_id')
    organ = tables.Column(accessor='cell.organ')
    dataset = tables.Column(accessor='cell.dataset')
    modality = tables.Column(accessor='cell.modality')
    protein_mean = tables.Column(accessor='cell.protein_mean')
    protein_total = tables.Column(accessor='cell.protein_total')
    protein_covar = tables.Column(accessor='cell.protein_covar')

    class Meta:
        model = models.Quant