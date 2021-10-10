import json
from typing import List

import numpy as np
from django.db.models import Case, IntegerField, Sum, When
from rest_framework import serializers

from .apps import (
    atac_adata,
    atac_percentages,
    atac_pvals,
    codex_adata,
    codex_percentages,
    rna_adata,
    rna_percentages,
    rna_pvals,
)
from .filters import get_cells_list, split_at_comparator
from .models import (
    Cell,
    Cluster,
    Dataset,
    Gene,
    Modality,
    Organ,
    Protein,
    QuerySet,
    StatReport,
)


def infer_values_type(values: List) -> str:

    print(values)

    values = [
        split_at_comparator(item)[0].strip()
        if len(split_at_comparator(item)) > 0
        else item.strip()
        for item in values
    ]

    if len(values) == 0:
        return None

    values_up = [value.upper() for value in values]
    values = values + values_up

    """Assumes a non-empty list of one one type of entity, and no identifier collisions across entity types"""
    if Gene.objects.filter(gene_symbol__in=values).count() > 0:
        return "gene"
    if Protein.objects.filter(protein_id__in=values).count() > 0:
        return "protein"
    if Cluster.objects.filter(grouping_name__in=values).count() > 0:
        return "cluster"
    if Organ.objects.filter(grouping_name__in=values).count() > 0:
        return "organ"
    values.sort()
    raise ValueError(
        f"Value type could not be inferred. None of {values} recognized as gene, protein, cluster, or organ"
    )


def get_quant_value(cell_id, gene_symbol, modality):
    if modality == "codex":
        adata = codex_adata
        var_adata = adata[:, [gene_symbol]]
        cell_and_var_adata = var_adata[[cell_id], :]
        val = cell_and_var_adata.X.flatten()[0]

    elif modality == "rna":
        adata = rna_adata
    elif modality == "atac":
        adata = atac_adata

    if modality in ["rna", "atac"]:
        var_adata = adata[:, [gene_symbol]]
        cell_and_var_adata = var_adata[[cell_id], :]
        cell_and_var_x = cell_and_var_adata.X.todense().flatten()[0]
        if isinstance(cell_and_var_x, np.ndarray):
            cell_and_var_x = cell_and_var_x[0]
        val = cell_and_var_x

    return val


def get_precomputed_percentage(uuid, values_type, include_values):
    modality = Dataset.objects.filter(uuid=uuid).first().modality.modality_name
    if modality == "rna":
        df = rna_percentages
    elif modality == "atac":
        df = atac_percentages
    elif modality == "codex":
        df = codex_percentages

    if isinstance(include_values, list):
        set_split = split_at_comparator(include_values[0])
    else:
        set_split = split_at_comparator(include_values)

    set_split = [item.strip() for item in set_split]
    var_id = set_split[0]
    cutoff = float(set_split[2])

    if var_id in list(df["var_id"].unique()) and cutoff in list(df["cutoff"].unique()):
        df = df[df["var_id"] == var_id]
        df = df[df["cutoff"] == cutoff]
        df = df[df["dataset"] == uuid]
        return list(df["percentage"])[0]

    return None


def get_percentage(uuid, values_type, include_values):

    precomputed_percentage = get_precomputed_percentage(uuid, values_type, include_values)
    if precomputed_percentage:
        print("Precomputed percentage found")
        return precomputed_percentage

    print("Precomputed percentage not found")
    query_params = {
        "input_type": values_type,
        "input_set": include_values,
        "logical_operator": "and",
    }
    dataset = Dataset.objects.filter(uuid=uuid).first()
    if values_type == "gene" and dataset:
        query_params["genomic_modality"] = dataset.modality.modality_name
    var_cell_pks = get_cells_list(query_params, input_set=include_values).values_list(
        "pk", flat=True
    )
    var_cells = (
        Cell.objects.filter(pk__in=var_cell_pks).only("pk", "dataset").select_related("dataset")
    )

    aggregate_kwargs = {
        str(dataset.pk): Sum(Case(When(dataset=dataset.pk, then=1), output_field=IntegerField()))
    }

    dataset_count = Cell.objects.filter(dataset=dataset.pk).count()

    count = int(var_cells.aggregate(**aggregate_kwargs)[str(dataset.pk)])
    percentage = count / dataset_count * 100
    return percentage


def get_modality_pval(pval_df, identifier, set_type, var_id):
    if set_type in ["organ", "cluster"]:
        df = pval_df[pval_df["grouping_name"] == identifier]
        df = df[df["gene_id"] == var_id]

    elif set_type in ["gene"]:
        df = pval_df[pval_df["gene_id"] == identifier]
        df = df[df["grouping_name"] == var_id]

    value = list(df["value"])[0] if len(list(df["value"])) >= 1 else None
    return value


def get_p_values(identifier, set_type, var_id, var_type, statistic="mean"):

    rna_value = get_modality_pval(rna_pvals, identifier, set_type, var_id)
    atac_value = get_modality_pval(atac_pvals, identifier, set_type, var_id)

    if rna_value is not None and atac_value is not None:
        return min(rna_value, atac_value)
    elif rna_value is not None:
        return rna_value
    elif atac_value is not None:
        return atac_value


class ModalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Modality
        fields = ["modality_name"]


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ["uuid"]


class ClusterSerializer(serializers.ModelSerializer):
    dataset = serializers.CharField(read_only=True, source="dataset.uuid", default=None)

    class Meta:
        model = Cluster
        fields = ["cluster_method", "cluster_data", "grouping_name", "dataset"]


class CellSerializer(serializers.ModelSerializer):
    modality = serializers.CharField(read_only=True, source="modality.modality_name")
    dataset = serializers.CharField(read_only=True, source="dataset.uuid")
    organ = serializers.CharField(read_only=True, source="organ.grouping_name")
    clusters = serializers.StringRelatedField(many=True)

    class Meta:
        model = Cell
        fields = [
            "cell_id",
            "modality",
            "dataset",
            "organ",
            "clusters",
        ]


class OrganSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organ
        fields = ["grouping_name"]


class GeneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gene
        fields = ["gene_symbol", "go_terms"]


class ProteinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Protein
        fields = ["protein_id", "go_terms"]


class CellAndValuesSerializer(serializers.ModelSerializer):

    modality = serializers.CharField(read_only=True, source="modality.modality_name")
    dataset = serializers.CharField(read_only=True, source="dataset.uuid")
    organ = serializers.CharField(read_only=True, source="organ.grouping_name")
    clusters = serializers.StringRelatedField(many=True)
    values = serializers.SerializerMethodField(method_name="get_values")

    class Meta:
        model = Cell
        fields = [
            "cell_id",
            "modality",
            "dataset",
            "organ",
            "clusters",
            "values",
        ]

    def get_values(self, obj):
        request = self.context["request"]
        var_ids = request.POST.getlist("values_included")
        values_dict = {
            var_id: get_quant_value(obj.cell_id, var_id, obj.modality.modality_name)
            for var_id in var_ids
        }
        return values_dict


class GeneAndValuesSerializer(serializers.ModelSerializer):
    #    values = serializers.JSONField()
    #    gene = GeneSerializer(read_only=True)
    values = serializers.SerializerMethodField(method_name="get_values")

    class Meta:
        model = Gene
        fields = ["gene_symbol", "go_terms", "values"]

    def get_values(self, obj):
        request = self.context["request"]
        var_ids = request.POST.getlist("values_included")
        var_type = infer_values_type(var_ids)
        values_dict = {
            var_id: get_p_values(
                identifier=obj.gene_symbol, var_id=var_id, var_type=var_type, set_type="gene"
            )
            for var_id in var_ids
        }
        return values_dict


class OrganAndValuesSerializer(serializers.ModelSerializer):
    values = serializers.SerializerMethodField(method_name="get_values")

    class Meta:
        model = Organ
        fields = ["grouping_name", "values"]

    def get_values(self, obj):
        request = self.context["request"]
        var_ids = request.POST.getlist("values_included")
        var_type = infer_values_type(var_ids)
        values_dict = {
            var_id: get_p_values(
                identifier=obj.grouping_name, var_id=var_id, var_type=var_type, set_type="organ"
            )
            for var_id in var_ids
        }
        return values_dict


class ClusterAndValuesSerializer(serializers.ModelSerializer):
    values = serializers.SerializerMethodField(method_name="get_values")
    dataset = serializers.CharField(read_only=True, source="dataset.uuid", default=None)

    class Meta:
        model = Cluster
        fields = ["cluster_method", "cluster_data", "grouping_name", "dataset", "values"]

    def get_values(self, obj):
        request = self.context["request"]
        var_ids = request.POST.getlist("values_included")
        var_type = infer_values_type(var_ids)
        values_dict = {
            var_id: get_p_values(
                identifier=obj.grouping_name, var_id=var_id, var_type=var_type, set_type="cluster"
            )
            for var_id in var_ids
        }
        return values_dict


class DatasetAndValuesSerializer(serializers.ModelSerializer):
    values = serializers.SerializerMethodField(method_name="get_values")

    class Meta:
        model = Dataset
        fields = ["uuid", "values"]

    def get_values(self, obj):
        request = self.context["request"]
        conditions = request.POST.getlist("values_included")
        if len(conditions) == 0:
            return None
        else:
            values_type = infer_values_type(conditions)
            return get_percentage(obj.uuid, values_type, conditions[0])


class QuerySetSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuerySet
        fields = ["query_handle", "set_type"]


class QuerySetCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuerySet
        fields = ["query_handle", "set_type", "count"]


class StatReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatReport
        fields = [
            "query_handle",
            "var_id",
            "statistic_type",
            "rna_value",
            "atac_value",
            "codex_value",
            "num_cells_excluded",
        ]
