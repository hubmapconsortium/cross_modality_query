# Generated by Django 3.2 on 2021-05-03 18:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("query_app", "0002_dataset_and_values"),
    ]

    operations = [
        migrations.CreateModel(
            name="StatReport",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("query_handle", models.TextField()),
                ("var_id", models.TextField()),
                ("statistic_type", models.TextField()),
                ("rna_value", models.FloatField(null=True)),
                ("atac_value", models.FloatField(null=True)),
                ("codex_value", models.FloatField(null=True)),
                ("num_cells_excluded", models.IntegerField(null=True)),
            ],
        ),
    ]
