from rest_framework import serializers

from .models import (
    Cell,
    CellAndValues,
    Cluster,
    ClusterAndValues,
    Dataset,
    Gene,
    GeneAndValues,
    Modality,
    Organ,
    OrganAndValues,
    Protein,
    QuerySet,
)


class ModalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Modality
        fields = ["modality_name"]


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ["uuid"]


class ClusterSerializer(serializers.ModelSerializer):
    dataset = serializers.CharField(read_only=True, source = 'dataset.uuid')
    class Meta:
        model = Cluster
        fields = ["cluster_method", "cluster_data", "grouping_name", "dataset"]


class CellSerializer(serializers.ModelSerializer):
    modality = serializers.CharField(read_only=True, source='modality.modality_name')
    dataset = serializers.CharField(read_only=True, source = 'dataset.uuid')
    organ = serializers.CharField(read_only=True, source= 'organ_grouping.name')
#    clusters = serializers.RelatedField(read_only=True, many=True)

    class Meta:
        model = Cell
        fields = [
            "cell_id",
            "modality",
            "dataset",
            "organ",
            "clusters",
            "protein_mean",
            "protein_total",
            "protein_covar",
        ]


class OrganSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organ
        fields = ["grouping_name", "cells"]


class GeneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gene
        fields = ["gene_symbol", "go_terms"]


class ProteinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Protein
        fields = ["protein_id", "go_terms"]


class CellAndValuesSerializer(serializers.ModelSerializer):
    #    cell = CellSerializer(read_only=True)
    #    values = serializers.JSONField()
    modality = serializers.CharField(read_only=True, source='modality.modality_name')
    dataset = serializers.CharField(read_only=True, source = 'dataset.uuid')
    organ = serializers.CharField(read_only=True, source= 'organ_grouping.name')

    class Meta:
        model = CellAndValues
        #        fields = ['cell', 'values']
        fields = [
            "cell_id",
            "modality",
            "dataset",
            "organ",
            "protein_mean",
            "protein_total",
            "protein_covar",
            "organ",
            "values",
        ]


class GeneAndValuesSerializer(serializers.ModelSerializer):
    #    values = serializers.JSONField()
    #    gene = GeneSerializer(read_only=True)

    class Meta:
        model = GeneAndValues
        fields = ["gene_symbol", "go_terms", "values"]


#        fields = ['gene', 'values']


class OrganAndValuesSerializer(serializers.ModelSerializer):
    #    organ = serializers.RelatedField(read_only=True)
    #    values = serializers.JSONField()

    class Meta:
        model = OrganAndValues
        fields = ["grouping_name", "values"]

class ClusterAndValuesSerializer(serializers.ModelSerializer):

    dataset = serializers.CharField(read_only=True, source = 'dataset.uuid')

    class Meta:
        model = ClusterAndValues
        fields = ["grouping_name", "dataset", "values"]


class QuerySetSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuerySet
        fields = ["query_pickle_hash", "set_type"]

class QuerySetCountSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuerySet
        fields = ["query_pickle_hash", "set_type", "count"]