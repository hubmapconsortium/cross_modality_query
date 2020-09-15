from django.contrib.postgres.fields import ArrayField
from django.db import models


class Cell(models.Model):
    cell_id = models.CharField(db_index=True, max_length=60)
    modality = models.CharField(db_index=True, max_length=20)
    protein_mean = models.JSONField(db_index=True)
    protein_total = models.JSONField(db_index=True)
    protein_covar = models.JSONField(db_index=True)
    cell_shape = ArrayField(models.FloatField(), db_index=True)


#    groupings = models.ManyToManyField(Cell_Grouping, related_name='cells')

class Gene(models.Model):
    gene_symbol = models.CharField(db_index=True, max_length=20)
    go_terms = ArrayField(models.CharField(max_length=50), db_index=True)


#    groups = models.ManyToManyField(Cell_Grouping)
#    marker_groups = models.ManyToManyField(Cell_Grouping)

class CellGrouping(models.Model):
    group_type = models.CharField(db_index=True, max_length=20)
    group_id = models.CharField(db_index=True, max_length=20)
    cells = models.ManyToManyField(Cell, related_name='groupings')
    genes = models.ManyToManyField(Gene, related_name='groups')
    marker_genes = models.ManyToManyField(Gene, related_name='marker_groups')


# class Protein(models.Model):
#    protein_id = models.CharField(db_index=True, max_length=20)
#    go_terms = ArrayField(db_index=True)
#    groups = models.ManyToManyField(Cell_Grouping)
#    marker_groups = models.ManyToManyField(Cell_Grouping)

class RnaQuant(models.Model):
    cell_id = models.CharField(db_index=True, max_length=60)
    gene_id = models.CharField(db_index=True, max_length=20)
    value = models.FloatField(db_index=True)


class AtacQuant(models.Model):
    cell_id = models.CharField(db_index=True, max_length=60)
    gene_id = models.CharField(db_index=True, max_length=20)
    value = models.FloatField(db_index=True)

# class Metabolite(Base): __tablename__ = 'metabolite' metabolite_id = Column(String, primary_key=True) groups =
# relationship('Cell_Grouping', secondary=metabolite_groupings, back_populates='metabolites') marker_groups =
# relationship('Cell_Grouping', secondary=marker_metabolite_groupings, back_populates='marker_metabolites')

# class Motif(Base):
#    __tablename__ = 'motif'
#    motif_id = Column(String, primary_key=True)
#    groups = relationship('Cell_Grouping', secondary=motif_groupings, back_populates='motifs')
#    marker_groups = relationship('Cell_Grouping', secondary=marker_motif_groupings, back_populates='marker_motifs')
