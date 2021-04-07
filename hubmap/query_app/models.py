import json

import django.utils.timezone
from django.contrib.postgres.fields import ArrayField
from django.db import models

EXPIRATION_TIME = 14400  # 4 hours in seconds


class CellGrouping(models.Model):
    grouping_name = models.CharField(max_length=64, null=True)

    class Meta:
        abstract = True


class Modality(models.Model):
    modality_name = models.CharField(max_length=16)

    def __repr__(self):
        return self.modality_name

    def __str__(self):
        return "%s" % self.modality_name


class Dataset(CellGrouping):
    uuid = models.CharField(max_length=32)
    modality = models.ForeignKey(
        to=Modality, related_name="datasets", on_delete=models.CASCADE, null=True
    )

    def __repr__(self):
        return self.uuid

    def __str__(self):
        return "%s" % self.uuid


class Organ(CellGrouping):
    def __repr__(self):
        return self.grouping_name

    def __str__(self):
        return "%s" % self.grouping_name


class Cluster(CellGrouping):
    cluster_method = models.CharField(max_length=16)  # i.e. leiden, k means
    cluster_data = models.CharField(max_length=16)  # UMAP, protein mean, cell shape
    dataset = models.ForeignKey(
        to=Dataset, related_name="clusters", on_delete=models.CASCADE, null=True
    )


class Cell(models.Model):
    cell_id = models.CharField(db_index=True, max_length=128, null=True)
    modality = models.ForeignKey(to=Modality, on_delete=models.CASCADE, null=True)
    dataset = models.ForeignKey(
        to=Dataset, related_name="cells", on_delete=models.CASCADE, null=True
    )
    barcode = models.CharField(max_length=64, null=True)
    tile = models.CharField(max_length=32, null=True)
    mask_index = models.IntegerField(null=True)
    organ = models.ForeignKey(to=Organ, related_name="cells", on_delete=models.CASCADE, null=True)
    clusters = models.ManyToManyField(to=Cluster, related_name="cells")

    def __repr__(self):
        return self.cell_id

    def __str__(self):
        cell_dict = {
            "cell_id": self.cell_id,
            "modality": self.modality,
            "dataset": self.dataset,
            "organ": self.organ,
        }

        return json.dumps(cell_dict)


class Gene(models.Model):
    gene_symbol = models.CharField(db_index=True, max_length=64)
    go_terms = ArrayField(models.CharField(max_length=50), db_index=True, null=True, blank=True)

    def __repr__(self):
        return self.gene_symbol

    def __str__(self):
        return "%s" % self.gene_symbol


class Protein(models.Model):
    protein_id = models.CharField(db_index=True, max_length=32)
    go_terms = ArrayField(models.CharField(max_length=50), db_index=True, null=True, blank=True)

    def __repr__(self):
        return self.protein_id


class Quant(models.Model):
    q_cell_id = models.CharField(max_length=128, null=True, db_index=True)
    q_var_id = models.CharField(max_length=64, null=True, db_index=True)
    value = models.FloatField()

    class Meta:
        abstract = True


class RnaQuant(Quant):
    def __repr__(self):
        return str(self.value)


class AtacQuant(Quant):
    def __repr__(self):
        return str(self.value)


class CodexQuant(Quant):
    statistic = models.CharField(
        max_length=16, null=True, db_index=True
    )  # One of mean, total, covariance


#    region = models.CharField(
#        max_length=16, null=True
#    )  # One of nucleus, membrane, cytoplasm, cell


class PVal(models.Model):
    p_cluster = models.ForeignKey(to=Cluster, on_delete=models.CASCADE, null=True)
    p_organ = models.ForeignKey(to=Organ, on_delete=models.CASCADE, null=True)
    p_gene = models.ForeignKey(to=Gene, on_delete=models.CASCADE, null=True)
    modality = models.ForeignKey(to=Modality, on_delete=models.CASCADE, null=True)
    value = models.FloatField(null=True, db_index=True)

    def __repr__(self):
        return self.value


class CellAndValues(Cell):
    """A model used for storing and serializing cells and subsets of their expression values"""

    values = models.JSONField(null=True)
    created = models.DateTimeField(null=True, auto_now_add=True)


class OrganAndValues(Organ):
    values = models.JSONField(null=True)
    created = models.DateTimeField(null=True, auto_now_add=True)


class GeneAndValues(Gene):
    values = models.JSONField(null=True)
    created = models.DateTimeField(null=True, auto_now_add=True)


class ClusterAndValues(Cluster):
    values = models.JSONField(null=True)
    created = models.DateTimeField(null=True, auto_now_add=True)


class QuerySet(models.Model):
    query_pickle = models.BinaryField()
    query_handle = models.TextField()
    created = models.DateTimeField(null=True, auto_now_add=True)
    set_type = models.CharField(max_length=16)
    count = models.IntegerField(null=True)

    @property
    def is_expired(self):
        age = django.utils.timezone.now() - self.created
        return age.total_seconds() > EXPIRATION_TIME
