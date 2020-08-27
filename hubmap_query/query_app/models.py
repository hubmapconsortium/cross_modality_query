from typing import List, Tuple
import json
import pandas as pd
import operator

from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField


#Mappings from output set types to objects/tables we want to query
output_aspects = {'cell':Cell, 'gene':Gene, 'tissue_type':Cell_Grouping, 'dataset':Cell_Grouping, 'protein':Protein}
#Mappings from input set types to columns used to build condition
input_aspects = {'cell':cell_id, 'gene':genes,'marker_gene':marker_genes, 'tissue_type':tissue_type, 'dataset':dataset, 'protein':protein_mean, 'modality':modality}
#Mappings from string representations of logical operators to corresponding SQLalchemy functions
logical_operators = {'and':and_, 'or':or_}
comparator_dict = {'==': operator.eq, '!=': operator.ne, '>=':operator.ge, '>':operator.gt, '<=':operator.le, '<':operator.lt}


class Cell(models.Model):
    cell_id = models.CharField(db_index=True, max_length=60)
    modality = models.CharField(db_index=True, max_length=20)
    protein_mean = JSONField(db_index=True)
    protein_total = JSONField(db_index=True)
    protein_covar = JSONField(db_index=True)
    cell_shape = ArrayField(db_index=True)
    groupings = models.ManyToManyField(Cell_Grouping)

class Cell_Grouping(models.Model):
    group_type = models.CharField(db_index=True, max_length=20)
    group_id = models.CharField(db_index=True, max_length=20)
#    cells = models.ManyToManyField(Cell)
    genes = models.ManyToManyField(Gene)
    marker_genes = models.ManyToManyField(Gene)

class Gene(models.Model):
    gene_symbol = models.CharField(db_index=True, max_length=20)
    go_terms = ArrayField(db_index=True)
#    groups = models.ManyToManyField(Cell_Grouping)
#    marker_groups = models.ManyToManyField(Cell_Grouping)

class Protein(models.Model):
    protein_id = models.CharField(db_index=True, max_length=20)
    go_terms = ArrayField(db_index=True)
#    groups = models.ManyToManyField(Cell_Grouping)
#    marker_groups = models.ManyToManyField(Cell_Grouping)

class RNA_Quant(models.Model):
    cell_id = models.CharField(db_index=True, max_length=60)
    gene_id = models.CharField(db_index=True, max_length=20)
    value = models.FloatField(db_index=True)

class ATAC_Quant(models.Model):
    cell_id = models.CharField(db_index=True, max_length=60)
    gene_id = models.CharField(db_index=True, max_length=20)
    value = models.FloatField(db_index=True)


#class Metabolite(Base):
#    __tablename__ = 'metabolite'
#    metabolite_id = Column(String, primary_key=True)
#    groups = relationship('Cell_Grouping', secondary=metabolite_groupings, back_populates='metabolites')
#    marker_groups = relationship('Cell_Grouping', secondary=marker_metabolite_groupings, back_populates='marker_metabolites')

#class Motif(Base):
#    __tablename__ = 'motif'
#    motif_id = Column(String, primary_key=True)
#    groups = relationship('Cell_Grouping', secondary=motif_groupings, back_populates='motifs')
#    marker_groups = relationship('Cell_Grouping', secondary=marker_motif_groupings, back_populates='marker_motifs')
