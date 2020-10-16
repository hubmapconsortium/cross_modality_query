from rest_framework import serializers

from .models import (
    Cell,
    Gene,
    Organ,
    Protein,
    PVal,
    Quant,
)


class CellSerializer(serializers.ModelSerializer):
    modality = serializers.StringRelatedField()
    dataset = serializers.StringRelatedField()
    organ = serializers.StringRelatedField()

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


class GenePValSerializer(serializers.ModelSerializer):
    class Meta:
        model = PVal
        fields = ['gene_id', 'value']


class OrganPValSerializer(serializers.ModelSerializer):
    class Meta:
        model = PVal
        fields = ['organ_name', 'value']


class CellQuantSerializer(serializers.ModelSerializer):
    quant_cell = serializers.StringRelatedField()

    class Meta:
        model = Quant
        fields = ['quant_cell', 'value']
