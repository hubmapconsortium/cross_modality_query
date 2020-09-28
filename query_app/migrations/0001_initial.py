# Generated by Django 3.1.1 on 2020-09-24 10:12

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AtacQuant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cell_id', models.CharField(db_index=True, max_length=60)),
                ('gene_id', models.CharField(db_index=True, max_length=20)),
                ('value', models.FloatField(db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='Cell',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cell_id', models.CharField(db_index=True, max_length=60)),
                ('modality', models.CharField(db_index=True, max_length=20)),
                ('protein_mean', models.JSONField(blank=True, db_index=True, null=True)),
                ('protein_total', models.JSONField(blank=True, db_index=True, null=True)),
                ('protein_covar', models.JSONField(blank=True, db_index=True, null=True)),
                ('cell_shape', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), blank=True, db_index=True, null=True, size=None)),
            ],
        ),
        migrations.CreateModel(
            name='Gene',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gene_symbol', models.CharField(db_index=True, max_length=20)),
                ('go_terms', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), blank=True, db_index=True, null=True, size=None)),
            ],
        ),
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('input_type', models.CharField(choices=[('Cell', 'Cell'), ('Gene', 'Gene'), ('Organ', 'Organ')], max_length=5)),
                ('input_set', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1024), size=None)),
                ('logical_operator', models.CharField(choices=[('and', 'or'), ('or', 'or')], max_length=3)),
                ('marker', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='RnaQuant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cell_id', models.CharField(db_index=True, max_length=60)),
                ('gene_id', models.CharField(db_index=True, max_length=20)),
                ('value', models.FloatField(db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='CellGrouping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group_type', models.CharField(db_index=True, max_length=20)),
                ('group_id', models.CharField(db_index=True, max_length=20)),
                ('cells', models.ManyToManyField(related_name='groupings', to='query_app.Cell')),
                ('genes', models.ManyToManyField(related_name='groups', to='query_app.Gene')),
                ('marker_genes', models.ManyToManyField(related_name='marker_groups', to='query_app.Gene')),
            ],
        ),
    ]
