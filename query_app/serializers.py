from rest_framework import serializers

from .models import (
    Cell,
    CellGrouping,
    Gene,
    # Protein,
)


class CellSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cell
        fields = ['cell_id', 'modality', 'protein_mean', 'protein_total', 'protein_covar', 'cell_shape', 'groupings']


class CellGroupingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CellGrouping
        fields = ['group_type', 'group_id', 'cells', 'genes', 'marker_genes']


class GeneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gene
        fields = ['gene_symbol', 'go_terms', 'groups', 'marker_groups']

# class ProteinSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Protein
#        fields = ['protein_id', 'go_terms']
