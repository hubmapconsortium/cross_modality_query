import json
from typing import List

from django.db.models import Case, IntegerField, Sum, When
from rest_framework import serializers

from .filters import get_cells_list, split_at_comparator
from .models import (
    AtacQuant,
    Cell,
    Cluster,
    CodexQuant,
    Dataset,
    Gene,
    Modality,
    Organ,
    PrecomputedPercentage,
    Protein,
    PVal,
    QuerySet,
    RnaQuant,
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
    if modality == "rna":
        quant = (
            RnaQuant.objects.filter(q_var_id__iexact=gene_symbol).filter(q_cell_id=cell_id).first()
        )
    if modality == "atac":
        quant = (
            AtacQuant.objects.filter(q_var_id__iexact=gene_symbol)
            .filter(q_cell_id=cell_id)
            .first()
        )
    elif modality == "codex":
        quant = (
            CodexQuant.objects.filter(q_var_id__iexact=gene_symbol)
            .filter(q_cell_id=cell_id)
            .first()
        )
        print("Quant found")

    return 0.0 if quant is None else quant.value


def get_percentage(uuid, values_type, include_values):
    if len(include_values) == 1:
        split = split_at_comparator(include_values[0])
        if len(split) > 1:
            var_id = split[0]
            cutoff = split[2]
            cached_value = (
                PrecomputedPercentage.objects.filter(dataset__uuid=uuid)
                .filter(var_id=var_id)
                .filter(cutoff=cutoff)
                .first()
                .percentage
            )
            if cached_value:
                return cached_value

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


def get_p_values(identifier, set_type, var_id, var_type, statistic="mean"):

    filter_kwargs_one_dict = {
        "gene": {f"p_{var_type}__grouping_name": var_id},
        "organ": {"p_gene__gene_symbol": var_id},
        "cluster": {"p_gene__gene_symbol": var_id},
    }
    filter_kwargs_two_dict = {
        "gene": {"p_gene__gene_symbol": identifier},
        "organ": {"p_organ__grouping_name": identifier},
        "cluster": {"p_cluster__grouping_name": identifier},
    }
    values_list_args_dict = {
        "gene": {
            "organ": ["p_organ__grouping_name", "value"],
            "cluster": ["p_cluster__grouping_name", "value"],
        },
        "organ": {"gene": ["p_gene__gene_symbol", "value"]},
        "cluster": {"gene": ["p_gene__gene_symbol", "value"]},
    }

    filter_kwargs_one = filter_kwargs_one_dict[set_type]
    filter_kwargs_two = filter_kwargs_two_dict[set_type]
    values_list_args = values_list_args_dict[set_type][var_type]

    pval = (
        PVal.objects.filter(**filter_kwargs_one)
        .filter(**filter_kwargs_two)
        .order_by("value")
        .values_list(*values_list_args)
    )

    value = pval[0][1]

    return value


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


class CellValuesSerializer(serializers.ModelSerializer):

    values = serializers.SerializerMethodField(method_name="get_values")

    class Meta:
        model = Cell
        #        fields = ['cell', 'values']
        fields = [
            "values",
        ]

    def get_values(self, obj):
        request = self.context["request"]
        var_ids = request.POST.getlist("values_included")
        values_dict = {
            var_id: get_quant_value(obj.cell_id, var_id, obj.modality.modality_name)
            for var_id in var_ids
        }
        return json.dumps(values_dict)
