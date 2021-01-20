import json

from django.contrib.postgres.fields import ArrayField
from django.db import models


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
    protein_mean = models.JSONField(db_index=True, null=True, blank=True)
    protein_total = models.JSONField(db_index=True, null=True, blank=True)
    protein_covar = models.JSONField(db_index=True, null=True, blank=True)
    cell_shape = ArrayField(models.FloatField(), db_index=True, null=True, blank=True)

    def __repr__(self):
        return self.cell_id

    def __str__(self):

        cell_dict = {
            "cell_id": self.cell_id,
            "modality": self.modality,
            "dataset": self.dataset,
            "organ": self.organ,
            "protein_mean": self.protein_mean,
            "protein_total": self.protein_total,
            "protein_covar": self.protein_covar,
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
    statistic = models.CharField(max_length=16, null=True)  # One of mean, total, covariance


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


class OrganAndValues(Organ):
    values = models.JSONField(null=True)


class GeneAndValues(Gene):
    values = models.JSONField(null=True)


class ClusterAndValues(Cluster):
    values = models.JSONField(null=True)


class QuerySet(models.Model):
    query_pickle = models.BinaryField()
    query_pickle_hash = models.TextField()
    created = models.DateTimeField(null=True)
    set_type = models.CharField(max_length=16)
    count = models.IntegerField(null=True)


class Query(models.Model):
    input_type = models.CharField(
        max_length=5, choices=(("Cell", "Cell"), ("Gene", "Gene"), ("Organ", "Organ"))
    )
    input_set = ArrayField(base_field=models.CharField(max_length=1024))
    logical_operator = models.CharField(max_length=3, choices=(("and", "or"), ("or", "or")))
