from rest_framework import serializers

from .models import (
    Cell,
    Gene,
    Organ,
    Protein,
)


class CellSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cell
        fields = ['cell_id', 'modality', 'dataset', 'tissue_type', 'protein_mean', 'protein_total', 'protein_covar', 'cell_shape', 'organ']


class OrganSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organ
        fields = ['organ_name', 'cells', 'genes', 'marker_genes']


class GeneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gene
        fields = ['gene_symbol', 'go_terms', 'organs', 'marker_organs']

class ProteinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Protein
        fields = ['protein_id', 'go_terms']
