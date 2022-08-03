# Generated by Django 4.0.6 on 2022-08-03 12:55

from django.db import migrations, models
import query_app.models


class Migration(migrations.Migration):

    dependencies = [
        ('query_app', '0007_dataset_annotation_metadata'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AtacQuant',
        ),
        migrations.DeleteModel(
            name='CodexQuant',
        ),
        migrations.RemoveField(
            model_name='pval',
            name='modality',
        ),
        migrations.RemoveField(
            model_name='pval',
            name='p_cluster',
        ),
        migrations.RemoveField(
            model_name='pval',
            name='p_gene',
        ),
        migrations.RemoveField(
            model_name='pval',
            name='p_organ',
        ),
        migrations.DeleteModel(
            name='RnaQuant',
        ),
        migrations.DeleteModel(
            name='StatReport',
        ),
        migrations.AddField(
            model_name='gene',
            name='summary',
            field=models.JSONField(default=query_app.models.summary_default),
        ),
        migrations.AddField(
            model_name='protein',
            name='summary',
            field=models.JSONField(default=query_app.models.summary_default),
        ),
        migrations.DeleteModel(
            name='PVal',
        ),
    ]
