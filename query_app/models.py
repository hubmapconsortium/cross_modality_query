from django.contrib.postgres.fields import ArrayField
from django.db import models


class Cell(models.Model):
    cell_id = models.CharField(db_index=True, max_length=60, null=True)
    modality = models.CharField(db_index=True, max_length=20, null=True)
    dataset = models.CharField(db_index=True, max_length=50, null=True)
    tissue_type = models.CharField(db_index=True, max_length=50, null=True)
    protein_mean = models.JSONField(db_index=True, null=True, blank=True)
    protein_total = models.JSONField(db_index=True, null=True, blank=True)
    protein_covar = models.JSONField(db_index=True, null=True, blank=True)
    cell_shape = ArrayField(models.FloatField(), db_index=True, null=True, blank=True)


class Gene(models.Model):
    gene_symbol = models.CharField(db_index=True, max_length=20)
    go_terms = ArrayField(models.CharField(max_length=50), db_index=True, null=True, blank=True)


class CellGrouping(models.Model):
    group_type = models.CharField(db_index=True, max_length=20)
    group_id = models.CharField(db_index=True, max_length=20)
    cells = models.ManyToManyField(Cell, related_name='groupings')
    genes = models.ManyToManyField(Gene, related_name='groups')
    marker_genes = models.ManyToManyField(Gene, related_name='marker_groups')


class Protein(models.Model):
    protein_id = models.CharField(db_index=True, max_length=20)
    go_terms = ArrayField(models.CharField(max_length=50), db_index=True, null=True, blank=True)


#    groups = models.ManyToManyField(Cell_Grouping)
#    marker_groups = models.ManyToManyField(Cell_Grouping)

class RnaQuant(models.Model):
    cell_id = models.CharField(db_index=True, max_length=60)
    gene_id = models.CharField(db_index=True, max_length=20)
    value = models.FloatField(db_index=True)


class AtacQuant(models.Model):
    cell_id = models.CharField(db_index=True, max_length=60)
    gene_id = models.CharField(db_index=True, max_length=20)
    value = models.FloatField(db_index=True)


class Query(models.Model):
    input_type = models.CharField(max_length=5, choices=(('Cell', 'Cell'), ('Gene', 'Gene'), ('Organ', 'Organ')))
    input_set = ArrayField(base_field=models.CharField(max_length=1024))
    logical_operator = models.CharField(max_length=3, choices=(('and', 'or'), ('or', 'or')))
    marker = models.BooleanField()
