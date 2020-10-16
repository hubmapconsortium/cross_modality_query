from django.contrib.postgres.fields import ArrayField
from django.db import models
import json


class Modality(models.Model):
    modality_name = models.CharField(max_length=10)

    def __repr__(self):
        return self.modality_name

    def __str__(self):
        return '%s' % self.modality_name


class Dataset(models.Model):
    uuid = models.CharField(max_length=32)
    modality = models.ForeignKey(to=Modality, related_name='datasets', on_delete=models.CASCADE, null=True)

    def __repr__(self):
        return self.uuid

    def __str__(self):
        return '%s' % self.uuid


class Gene(models.Model):
    gene_symbol = models.CharField(db_index=True, max_length=20)
    go_terms = ArrayField(models.CharField(max_length=50), db_index=True, null=True, blank=True)

    def __repr__(self):
        return self.gene_symbol

    def __str__(self):
        return '%s' % self.gene_symbol


class Organ(models.Model):
    organ_name = models.CharField(db_index=True, max_length=20)

    def __repr__(self):
        return self.organ_name

    def __str__(self):
        return '%s' % self.organ_name


class Cell(models.Model):
    cell_id = models.CharField(db_index=True, max_length=60, null=True)
    modality = models.ForeignKey(to=Modality, on_delete=models.CASCADE, null=True)
    dataset = models.ForeignKey(to=Dataset, related_name='cells', on_delete=models.CASCADE, null=True)
    organ = models.ForeignKey(to=Organ, related_name='cells', on_delete=models.CASCADE, null=True)
    protein_mean = models.JSONField(db_index=True, null=True, blank=True)
    protein_total = models.JSONField(db_index=True, null=True, blank=True)
    protein_covar = models.JSONField(db_index=True, null=True, blank=True)
    cell_shape = ArrayField(models.FloatField(), db_index=True, null=True, blank=True)

    def __repr__(self):
        return self.cell_id

    def __str__(self):
        cell_dict = {'cell_id': self.cell_id, 'modality': self.modality, 'dataset': self.dataset, 'organ': self.organ,
                     'protein_mean': self.protein_mean, 'protein_total': self.protein_total,
                     'protein_covar': self.protein_covar}
        return json.dumps(cell_dict)


class Protein(models.Model):
    protein_id = models.CharField(db_index=True, max_length=20)
    go_terms = ArrayField(models.CharField(max_length=50), db_index=True, null=True, blank=True)

    def __repr__(self):
        return self.protein_id


class Quant(models.Model):
    cell_id = models.CharField(db_index=True, max_length=60)
    quant_cell = models.ForeignKey(to=Cell, on_delete=models.CASCADE)
    gene_id = models.CharField(db_index=True, max_length=20)
    modality = models.ForeignKey(to=Modality, related_name='quants', on_delete=models.CASCADE, null=True)
    value = models.FloatField(db_index=True)

    def __repr__(self):
        return self.value


class PVal(models.Model):
    organ_name = models.CharField(max_length=20, db_index=True)
    gene_id = models.CharField(max_length=20, db_index=True)
    value = models.IntegerField()

    def __repr__(self):
        return self.value


class Query(models.Model):
    input_type = models.CharField(max_length=5, choices=(('Cell', 'Cell'), ('Gene', 'Gene'), ('Organ', 'Organ')))
    input_set = ArrayField(base_field=models.CharField(max_length=1024))
    logical_operator = models.CharField(max_length=3, choices=(('and', 'or'), ('or', 'or')))
