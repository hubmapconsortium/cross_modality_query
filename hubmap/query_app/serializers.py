from rest_framework import serializers

from .models import (
    Cell,
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


class CellSerializer(serializers.ModelSerializer):
    modality = serializers.RelatedField(read_only=True)
    dataset = serializers.RelatedField(read_only=True)
    organ = serializers.RelatedField(read_only=True)

    class Meta:
        model = Cell
        fields = ['cell_id', 'modality', 'dataset', 'organ', 'protein_mean', 'protein_total', 'protein_covar',
                  'cell_shape', 'organ']


class OrganSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organ
        fields = ['organ_name', 'cells']


class GeneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gene
        fields = ['gene_symbol', 'go_terms']


class ProteinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Protein
        fields = ['protein_id', 'go_terms']


class CellAndValuesSerializer(serializers.ModelSerializer):
    cell = serializers.RelatedField(read_only=True)

    class Meta:
        model = CellAndValues
        fields = ['cell_id', 'dataset', 'organ', 'protein_mean', 'protein_total', 'protein_covar',
                  'organ', 'values']


class GeneAndValuesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneAndValues
        fields = ['gene_symbol', 'go_terms', 'values']


class OrganAndValuesSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganAndValues
        fields = ['organ_name', 'values']


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
