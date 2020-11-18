from rest_framework import serializers

from .models import (
    Cell,
    Cluster,
    CellAndValues,
    Dataset,
    Gene,
    GeneAndValues,
    Organ,
    OrganAndValues,
    Modality,
    Protein,
    CellQueryResults,
    GeneQueryResults,
    OrganQueryResults,
)


class ModalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Modality
        fields = ['modality_name']


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['uuid']


class ClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cluster
        fields = ['cluster_method', 'cluster_data', 'grouping_name']


class CellSerializer(serializers.ModelSerializer):
    modality = serializers.RelatedField(read_only=True)
    dataset = serializers.RelatedField(read_only=True)
    organ = serializers.RelatedField(read_only=True)
    clusters = serializers.RelatedField(read_only=True, many=True)


    class Meta:
        model = Cell
        fields = ['cell_id', 'modality', 'dataset', 'organ', 'clusters', 'protein_mean', 'protein_total', 'protein_covar']


class OrganSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organ
        fields = ['grouping_name', 'cells']


class GeneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gene
        fields = ['gene_symbol', 'go_terms']


class ProteinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Protein
        fields = ['protein_id', 'go_terms']


class CellAndValuesSerializer(serializers.ModelSerializer):
#    cell = CellSerializer(read_only=True)
#    values = serializers.JSONField()

    class Meta:
        model = CellAndValues
#        fields = ['cell', 'values']
        fields = ['cell_id', 'dataset', 'organ', 'protein_mean', 'protein_total', 'protein_covar',
                  'organ', 'values']


class GeneAndValuesSerializer(serializers.ModelSerializer):
#    values = serializers.JSONField()
#    gene = GeneSerializer(read_only=True)

    class Meta:
        model = GeneAndValues
        fields = ['gene_symbol', 'go_terms', 'values']
#        fields = ['gene', 'values']

class OrganAndValuesSerializer(serializers.ModelSerializer):
#    organ = serializers.RelatedField(read_only=True)
#    values = serializers.JSONField()

    class Meta:
        model = OrganAndValues
        fields = ['grouping_name', 'values']


class CellQueryResultsSerializer(serializers.ModelSerializer):
    cells_and_values = serializers.RelatedField(read_only=True, many=True)

    class Meta:
        model = CellQueryResults
        fields = ['cells_and_values', 'mean', 'covariance', 'correlation']


class GeneQueryResultsSerializer(serializers.ModelSerializer):
    genes_and_values = serializers.RelatedField(read_only=True, many=True)

    class Meta:
        model = GeneQueryResults
        fields = ['genes_and_values', 'mean', 'covariance', 'correlation']


class OrganQueryResultsSerializer(serializers.ModelSerializer):
    organs_and_values = serializers.RelatedField(read_only=True, many=True)

    class Meta:
        model = OrganQueryResults
        fields = ['organs_and_values', 'mean', 'covariance', 'correlation']
