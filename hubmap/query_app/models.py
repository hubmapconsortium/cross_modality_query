from django.contrib.postgres.fields import ArrayField
from django.db import models

class Gene(models.Model):
    gene_symbol = models.CharField(db_index=True, max_length=20)
    go_terms = ArrayField(models.CharField(max_length=50), db_index=True, null=True, blank=True)


class Organ(models.Model):
    organ_name = models.CharField(db_index=True, max_length=20)
    genes = models.ManyToManyField(Gene, related_name='organs')
    marker_genes = models.ManyToManyField(Gene, related_name='marker_organs')


class Cell(models.Model):
    cell_id = models.CharField(db_index=True, max_length=60, null=True)
    modality = models.CharField(db_index=True, max_length=20, null=True)
    dataset = models.CharField(db_index=True, max_length=50, null=True)
    tissue_type = models.CharField(db_index=True, max_length=50, null=True)
    protein_mean = models.JSONField(db_index=True, null=True, blank=True)
    protein_total = models.JSONField(db_index=True, null=True, blank=True)
    protein_covar = models.JSONField(db_index=True, null=True, blank=True)
    cell_shape = ArrayField(models.FloatField(), db_index=True, null=True, blank=True)
    reporter = models.ForeignKey(Organ, related_name='cells', on_delete=models.CASCADE)


class Protein(models.Model):
    protein_id = models.CharField(db_index=True, max_length=20)
    go_terms = ArrayField(models.CharField(max_length=50), db_index=True, null=True, blank=True)


class Quant(models.Model):
    cell_id = models.CharField(db_index=True, max_length=60)
    gene_id = models.CharField(db_index=True, max_length=20)
    modality = models.CharField(db_index=True, max_length=20)
    value = models.FloatField(db_index=True)


class Query(models.Model):
    input_type = models.CharField(max_length=5, choices=(('Cell', 'Cell'), ('Gene', 'Gene'), ('Organ', 'Organ')))
    input_set = ArrayField(base_field=models.CharField(max_length=1024))
    logical_operator = models.CharField(max_length=3, choices=(('and', 'or'), ('or', 'or')))
    marker = models.BooleanField()
