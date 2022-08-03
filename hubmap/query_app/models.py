import json

from django.contrib.postgres.fields import ArrayField
from django.db import models

EXPIRATION_TIME = 14400  # 4 hours in seconds


def annotation_default():
    return {"is_annotated": False}

def summary_default():
    return {}


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
    annotation_metadata = models.JSONField(default=annotation_default)

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

    def __repr__(self):
        return self.grouping_name

    def __str__(self):
        return "%s" % self.grouping_name


class CellType(CellGrouping):
    def __repr__(self):
        return self.grouping_name

    def __str__(self):
        return "%s" % self.grouping_name


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
    cell_type = models.ForeignKey(
        to=CellType, related_name="cells", on_delete=models.CASCADE, null=True
    )

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
    summary = models.JSONField(default=summary_default)

    def __repr__(self):
        return self.gene_symbol

    def __str__(self):
        return "%s" % self.gene_symbol


class Protein(models.Model):
    protein_id = models.CharField(db_index=True, max_length=32)
    go_terms = ArrayField(models.CharField(max_length=50), db_index=True, null=True, blank=True)
    summary = models.JSONField(default=summary_default)

    def __repr__(self):
        return self.protein_id
