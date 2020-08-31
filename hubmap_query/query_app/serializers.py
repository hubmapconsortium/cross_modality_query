#@TODO: Write a serializer for each model in models.py
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import (
    Cell,
    Cell_Grouping,
    Gene,
    Protein,
    RNA_Quant,
    ATAC_Quant,
)

class CellSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cell
        fields = ['cell_id', 'modality', 'protein_mean', 'protein_total', 'protein_covar', 'cell_shape', 'groupings']

class Cell_GroupingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cell_Grouping
        fields = ['group_type', 'group_id', 'cells', 'genes', 'marker_genes']

class GeneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gene
        fields = ['gene_symbol', 'go_terms', 'groups', 'marker_groups']

#class ProteinSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Protein
#        fields = ['protein_id', 'go_terms']

class RNA_QuantSerializer(serializers.ModelSerializer):
    class Meta:
        model = RNA_Quant
        fields = ['cell_id', 'gene_id', 'value']

class ATAC_GroupingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ATAC_Quant
        fields = ['cell_id', 'gene_id', 'value']
