#!/usr/bin/env python

from typing import List
from pathlib import Path
from argparse import ArgumentParser
import pandas as pd
import json
import numpy as np
from django.db import transaction, connection
from django.core.cache import cache
from os import fspath

if __name__ == '__main__':
    import django

    django.setup()

from query_app.models import (
    Cell,
    Cluster,
    Dataset,
    Gene,
    Modality,
    Organ,
    Protein,
    PVal,
    RnaQuant,
    AtacQuant,
)


def load_cache():
    ids_list = Cell.objects.filter(modality__modality_name__in=['rna','atac']).values_list('id', 'cell_id')
    print(len(ids_list))
    ids_dict = {id[1]: id[0] for id in ids_list}
    print(len(ids_dict))
    cache.set_many(ids_dict, None)


def make_quants_csv(hdf_file):
    modality = hdf_file.stem

    csv_file = hdf_file.parent / Path(modality + '.csv')

    drop_quant_index(modality)

    sql = 'COPY query_app_' + modality + "quant(id, q_cell_id, q_gene_id, value)  FROM '" + fspath(csv_file) + "' CSV HEADER;"

    with connection.cursor() as cursor:
        cursor.execute(sql)

    create_quant_index(modality)


def create_quant_index(modality: str):
    sql = "CREATE INDEX " + modality + "_value_idx ON query_app_" + modality + "quant (value);"
    with connection.cursor() as cursor:
        cursor.execute(sql)


def drop_quant_index(modality: str):
    sql = 'DROP INDEX IF EXISTS ' + modality + '_value_idx;'
    with connection.cursor() as cursor:
        cursor.execute(sql)


def sanitize_string(string: str) -> str:
    return ''.join([char for char in string if char.isalnum() or char in '.-'])


def create_model(model_name: str, kwargs: dict):
    if model_name == 'cell':
        obj = Cell(**kwargs)
    elif model_name == 'gene':
        obj = Gene(**kwargs)
    elif model_name == 'organ':
        obj = Organ(**kwargs)
    elif model_name == 'protein':
        obj = Protein(**kwargs)
    elif model_name == 'pvalue':
        obj = PVal(**kwargs)
    else:
        obj = None
    return obj


def sanitize_nans(kwargs: dict) -> dict:
    cell_fields = ['cell_id', 'protein_mean', 'protein_total', 'protein_covar', 'dataset', 'modality', 'organ']

    if 'tissue_type' in kwargs.keys():
        kwargs['organ'] = kwargs['tissue_type']
        kwargs.pop('tissue_type')

    kwargs = {key: kwargs[key] for key in kwargs.keys() if key in cell_fields}

    for key in kwargs.keys():
        if type(kwargs[key]) == float and np.isnan(kwargs[key]):
            kwargs[key] = {}

    return kwargs


@transaction.atomic
def create_proteins(hdf_file):
    cell_df = pd.read_hdf(hdf_file, 'cell')
    protein_set = set({})
    for json_string in cell_df['protein_mean'].unique():
        if isinstance(json_string, str):
            json_dict = json.loads(json_string)
            for key in json_dict.keys():
                protein_set.add(key)
        else:
            print(json_string)

    proteins = [Protein(protein_id=protein) for protein in protein_set if Protein.objects.filter(protein_id__iexact=protein).first() is None]
    Protein.objects.bulk_create(proteins)


@transaction.atomic
def save_genes(gene_set: List[str]):
    genes = [Gene(gene_symbol=gene) for gene in gene_set]
    Gene.objects.bulk_create(genes)

def get_clusters(cell_df:pd.DataFrame):
    return cell_df[['cell_id', 'leiden']].to_dict('records')


def process_cell_records(cell_df: pd.DataFrame) -> List[dict]:
    if 'cell_id' not in cell_df.columns:
        cell_df['cell_id'] = cell_df.index

    records = cell_df.to_dict('records')
    sanitized_records = [sanitize_nans(record) for record in records]
    for record in sanitized_records:
        if None in record.values():
            print(record)
            sanitized_records.remove(record)

        if 'modality' in record.keys():
            record['modality'] = Modality.objects.filter(modality_name__icontains=record['modality']).first()
        record['dataset'] = Dataset.objects.filter(uuid__icontains=record['dataset']).first()
        if 'modality' not in record.keys():
            record['modality'] = record['dataset'].modality
        record['organ'] = Organ.objects.filter(grouping_name__icontains=record['organ']).first()

        for key in record.keys():
            if 'protein' in key and isinstance(record[key], str):
                record[key] = json.loads(record[key])
            if isinstance(record[key], dict):
                for protein_key in record[key].keys():
                    record[key][protein_key] = float(record[key][protein_key])

    return sanitized_records


def process_pval_args(kwargs: dict, modality: str):
    kwargs['p_gene'] = Gene.objects.filter(gene_symbol__iexact=sanitize_string(kwargs['gene_id'])[:64]).first()
    kwargs.pop('gene_id')

    if 'organ_name' in kwargs:
        kwargs['p_group'] = Organ.objects.filter(organ_name__iexact=kwargs['organ_name']).first()
        kwargs.pop('organ_name')
    elif 'cluster' in kwargs:
        kwargs['p_group'] = Cluster.objects.filter(cluster_name__iexact=kwargs['cluster']).first()
        kwargs.pop('cluster')

    kwargs['modality'] = Modality.objects.filter(modality_name__icontains=modality).first()
    return kwargs


@transaction.atomic
def df_to_db(df: pd.DataFrame, model_name: str, modality=None):
    if model_name == 'cell':

        kwargs_list = process_cell_records(df)
        objs = [create_model('cell', kwargs) for kwargs in kwargs_list]
        Cell.objects.bulk_create(objs)

        ids_list = Cell.objects.filter(modality__modality_name__iexact=modality).values_list('id', 'cell_id')
        ids_dict = {id[1]:id[0] for id in ids_list}
        cache.set_many(ids_dict, None)

    elif model_name == 'pvalue':
        kwargs_list = df.to_dict('records')
        processed_kwargs_list = [process_pval_args(kwargs, modality) for kwargs in kwargs_list]
        objs = [create_model('pvalue', kwargs) for kwargs in processed_kwargs_list]
        PVal.objects.bulk_create(objs)


def create_cells(hdf_file: Path):
    cell_df = pd.read_hdf(hdf_file, 'cell')
    cluster_assignments = []

    if hdf_file.stem in ['atac', 'rna']:
        cluster_assignments = get_clusters(cell_df)
    df_to_db(cell_df, 'cell')

    for ca in cluster_assignments:
        cell = Cell.objects.filter(cell_id__iexact=ca['cell_id']).first()
        cluster = Cluster.objects.filter(group_name__iexact=ca['leiden']).first()
        cell.clusters.add(cluster)


def create_genes(hdf_file: Path):
    pval_df = pd.read_hdf(hdf_file, 'organ')
    genes_to_create = [sanitize_string(gene)[:64] for gene in pval_df['gene_id'].unique() if
                       Gene.objects.filter(gene_symbol__icontains=sanitize_string(gene)[:64]).first() is None]
    save_genes(genes_to_create)

    return


def create_organs(hdf_file: Path):
    cell_df = pd.read_hdf(hdf_file, 'cell')
    if 'tissue_type' in cell_df.columns:
        organs = list(cell_df['tissue_type'].unique())
    elif 'organ_name' in cell_df.columns:
        organs = list(cell_df['organ_name'].unique())

    for organ_name in organs:
        if Organ.objects.filter(grouping_name__icontains=organ_name).first() is None:
            organ = Organ(grouping_name=organ_name)
            organ.save()

    return


def create_pvals(hdf_file: Path):
    modality = hdf_file.stem

    for grouping_type in ['organ', 'cluster']:
        with pd.HDFStore(hdf_file) as store:
            pval_df = store.get(grouping_type)
            df_to_db(pval_df, 'pvalue', modality)


def create_clusters(hdf_file: Path):

    if hdf_file.stem in ['atac', 'rna']:
        cluster_method = 'leiden'
        cluster_data = 'UMAP'
        with pd.HDFStore(hdf_file) as store:
            cluster_df = store.get('cluster')
            for cluster_name in cluster_df['cluster'].unique():
                cluster = Cluster(grouping_name=cluster_name, cluster_method=cluster_method, cluster_data=cluster_data)
                cluster.save()




def create_modality_and_datasets(hdf_file: Path):
    modality_name = hdf_file.stem
    modality = Modality.objects.filter(modality_name__iexact=modality_name).first()
    if modality is None:
        modality = Modality(modality_name=modality_name)
        modality.save()
    with pd.HDFStore(hdf_file) as store:
        cell_df = store.get('cell')
        for uuid in cell_df['dataset'].unique():
            dataset = Dataset(uuid=uuid[:32], modality=modality)
            dataset.save()


def load_rna(hdf_file: Path):
    Cell.objects.filter(modality__modality_name__icontains='rna').delete()
    RnaQuant.objects.all().delete()
    Dataset.objects.filter(modality__modality_name__icontains='rna').delete()
    Modality.objects.filter(modality_name__icontains='rna').delete()

    print('Old data deleted')
    create_modality_and_datasets(hdf_file)
    print('Modality and datasets created')
    create_organs(hdf_file)
    print('Organs created')
    create_clusters(hdf_file)
    print('Clusters created')
    create_cells(hdf_file)
    print('Cells created')
    make_quants_csv(hdf_file)
    print('Quants created')
    create_genes(hdf_file)
    print('Genes created')
    create_pvals(hdf_file)
    print('Pvals created')

    return


def load_atac(hdf_file):
    Cell.objects.filter(modality__modality_name__icontains='atac').delete()
    AtacQuant.objects.all().delete()
    Dataset.objects.filter(modality__modality_name__icontains='atac').delete()
    Modality.objects.filter(modality_name__icontains='atac').delete()

    print('Old data deleted')
    create_modality_and_datasets(hdf_file)
    print('Modality and datasets created')
    create_organs(hdf_file)
    print('Organs created')
    create_clusters(hdf_file)
    print('Clusters created')
    create_cells(hdf_file)
    print('Cells created')
    make_quants_csv(hdf_file)
    print('Quants created')
    create_genes(hdf_file)
    print('Genes created')
    create_pvals(hdf_file)
    print('Pvals created')

    return


def load_codex(hdf_file):
#    Cell.objects.filter(modality__modality_name__icontains='codex').delete()
#    Dataset.objects.filter(modality__modality_name__icontains='codex').delete()
#    Modality.objects.filter(modality_name__icontains='codex').delete()
#    Protein.objects.all().delete()

    print('Old data deleted')
    create_modality_and_datasets(hdf_file)
    print('Modality and datasets created')
    create_organs(hdf_file)
    print('Organs created')
    create_cells(hdf_file)
    print('Cells created')
    create_proteins(hdf_file)
    print('Proteins created')

    return


def main(hdf_files: List[Path]):
    for file in hdf_files:
        if 'rna' in file.stem:
            load_rna(file)
            print('RNA loaded')
        elif 'atac' in file.stem:
            load_atac(file)
            print('ATAC loaded')
        elif 'codex' in file.stem:
            load_codex(file)
            print('CODEX loaded')

    load_cache()


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('hdf_files', type=Path, nargs='+')
    args = p.parse_args()

    main(args.hdf_files)
