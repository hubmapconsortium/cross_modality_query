# Generated by Django 3.2 on 2021-05-03 02:59

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AtacQuant",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("q_cell_id", models.CharField(db_index=True, max_length=128, null=True)),
                ("q_var_id", models.CharField(db_index=True, max_length=64, null=True)),
                ("value", models.FloatField(db_index=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Cell",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("cell_id", models.CharField(db_index=True, max_length=128, null=True)),
                ("barcode", models.CharField(max_length=64, null=True)),
                ("tile", models.CharField(max_length=32, null=True)),
                ("mask_index", models.IntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Cluster",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("grouping_name", models.CharField(max_length=64, null=True)),
                ("cluster_method", models.CharField(max_length=16)),
                ("cluster_data", models.CharField(max_length=16)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CodexQuant",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("q_cell_id", models.CharField(db_index=True, max_length=128, null=True)),
                ("q_var_id", models.CharField(db_index=True, max_length=64, null=True)),
                ("value", models.FloatField(db_index=True)),
                ("statistic", models.CharField(db_index=True, max_length=16, null=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Dataset",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("grouping_name", models.CharField(max_length=64, null=True)),
                ("uuid", models.CharField(max_length=32)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Gene",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("gene_symbol", models.CharField(db_index=True, max_length=64)),
                (
                    "go_terms",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=50),
                        blank=True,
                        db_index=True,
                        null=True,
                        size=None,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Modality",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("modality_name", models.CharField(max_length=16)),
            ],
        ),
        migrations.CreateModel(
            name="Organ",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("grouping_name", models.CharField(max_length=64, null=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Protein",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("protein_id", models.CharField(db_index=True, max_length=32)),
                (
                    "go_terms",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=50),
                        blank=True,
                        db_index=True,
                        null=True,
                        size=None,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="QuerySet",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("query_pickle", models.BinaryField()),
                ("query_handle", models.TextField()),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("set_type", models.CharField(max_length=16)),
                ("count", models.IntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name="RnaQuant",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("q_cell_id", models.CharField(db_index=True, max_length=128, null=True)),
                ("q_var_id", models.CharField(db_index=True, max_length=64, null=True)),
                ("value", models.FloatField(db_index=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CellAndValues",
            fields=[
                (
                    "cell_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="query_app.cell",
                    ),
                ),
                ("values", models.JSONField(null=True)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
            ],
            bases=("query_app.cell",),
        ),
        migrations.CreateModel(
            name="ClusterAndValues",
            fields=[
                (
                    "cluster_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="query_app.cluster",
                    ),
                ),
                ("values", models.JSONField(null=True)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
            ],
            options={
                "abstract": False,
            },
            bases=("query_app.cluster",),
        ),
        migrations.CreateModel(
            name="GeneAndValues",
            fields=[
                (
                    "gene_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="query_app.gene",
                    ),
                ),
                ("values", models.JSONField(null=True)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
            ],
            bases=("query_app.gene",),
        ),
        migrations.CreateModel(
            name="OrganAndValues",
            fields=[
                (
                    "organ_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="query_app.organ",
                    ),
                ),
                ("values", models.JSONField(null=True)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
            ],
            options={
                "abstract": False,
            },
            bases=("query_app.organ",),
        ),
        migrations.CreateModel(
            name="PVal",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("value", models.FloatField(db_index=True, null=True)),
                (
                    "modality",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="query_app.modality",
                    ),
                ),
                (
                    "p_cluster",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="query_app.cluster",
                    ),
                ),
                (
                    "p_gene",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.CASCADE, to="query_app.gene"
                    ),
                ),
                (
                    "p_organ",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="query_app.organ",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="dataset",
            name="modality",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="datasets",
                to="query_app.modality",
            ),
        ),
        migrations.AddField(
            model_name="cluster",
            name="dataset",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="clusters",
                to="query_app.dataset",
            ),
        ),
        migrations.AddField(
            model_name="cell",
            name="clusters",
            field=models.ManyToManyField(related_name="cells", to="query_app.Cluster"),
        ),
        migrations.AddField(
            model_name="cell",
            name="dataset",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cells",
                to="query_app.dataset",
            ),
        ),
        migrations.AddField(
            model_name="cell",
            name="modality",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, to="query_app.modality"
            ),
        ),
        migrations.AddField(
            model_name="cell",
            name="organ",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cells",
                to="query_app.organ",
            ),
        ),
    ]
