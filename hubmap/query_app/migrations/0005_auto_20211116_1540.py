# Generated by Django 3.2.9 on 2021-11-16 15:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("query_app", "0004_trigram"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="cellandvalues",
            name="cell_ptr",
        ),
        migrations.RemoveField(
            model_name="clusterandvalues",
            name="cluster_ptr",
        ),
        migrations.RemoveField(
            model_name="datasetandvalues",
            name="dataset_ptr",
        ),
        migrations.RemoveField(
            model_name="geneandvalues",
            name="gene_ptr",
        ),
        migrations.RemoveField(
            model_name="organandvalues",
            name="organ_ptr",
        ),
        migrations.DeleteModel(
            name="QuerySet",
        ),
        migrations.DeleteModel(
            name="CellAndValues",
        ),
        migrations.DeleteModel(
            name="ClusterAndValues",
        ),
        migrations.DeleteModel(
            name="DatasetAndValues",
        ),
        migrations.DeleteModel(
            name="GeneAndValues",
        ),
        migrations.DeleteModel(
            name="OrganAndValues",
        ),
    ]
