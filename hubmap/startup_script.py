#!/usr/bin/env python

from functools import reduce
from typing import List
from pathlib import Path
from os import fspath
from argparse import ArgumentParser
import pandas as pd
import json
import numpy as np
from django.db import transaction

if __name__ == '__main__':
    import django

    django.setup()

from query_app.models import (
    Cell,
    Dataset,
    Gene,
    Modality,
    Organ,
    Protein,
    PVal,
    Quant,
)


def sanitize_string(string: str) -> str:
    return ''.join([char for char in string if char.isalnum() or char in '.-'])


def outer_join(df_1: pd.DataFrame, df_2: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([df_1, df_2], join='outer')


def create_model(model_name: str, kwargs: dict):
    if model_name == 'cell':
        obj = Cell(**kwargs)
    elif model_name == 'gene':
        obj = Gene(**kwargs)
    elif model_name == 'organ':
        obj = Organ(**kwargs)
    elif model_name == 'quant':
        obj = Quant(**kwargs)
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

    kwargs = {key:kwargs[key] for key in kwargs.keys() if key in cell_fields}

    for key in kwargs.keys():
        if type(kwargs[key]) == float and np.isnan(kwargs[key]):
            kwargs[key] = {}

    return kwargs


@transaction.atomic
def create_proteins(cell_df: pd.DataFrame):
    protein_set = set({})
    for json_string in cell_df['protein_mean'].unique():
        if isinstance(json_string, str):
            json_dict = json.loads(json_string)
            for key in json_dict.keys():
                protein_set.add(key)
        else:
            print(json_string)

    for protein in protein_set:
        p = Protein(protein_id=protein)
        p.save()


@transaction.atomic
def save_genes(gene_set: List[str]):
    for gene in gene_set:
        g = Gene(gene_symbol=gene)
        g.save()


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
        record['organ'] = Organ.objects.filter(organ_name__icontains=record['organ']).first()

        for key in record.keys():
            if 'protein' in key and isinstance(record[key], str):
                record[key] = json.loads(record[key])
            if isinstance(record[key], dict):
                for protein_key in record[key].keys():
                    record[key][protein_key] = float(record[key][protein_key])

    return sanitized_records


@transaction.atomic
def df_to_db(df: pd.DataFrame, model_name: str, modality=None):
    if model_name == 'organ':

        for i, row in df.iterrows():
            kwargs = {'organ_name': row['organ_name']}

            obj = create_model(model_name, kwargs)
            obj.save()


    elif model_name == 'quant':
        modality = Modality.objects.filter(modality_name__icontains=modality).first()
        dict_list = [{'cell_id': i, 'gene_id': column, 'modality': modality, 'value': df.at[i, column]} for i in
                     df.index for column in df.columns]
        for kwargs in dict_list:
            cell = Cell.objects.filter(cell_id__icontains=kwargs['cell_id']).first()
            kwargs['quant_cell'] = cell
            obj = create_model('quant', kwargs)
            obj.save()

    elif model_name == 'cell':

        kwargs_list = process_cell_records(df)

        for kwargs in kwargs_list:
            obj = create_model('cell', kwargs)
            obj.save()

    elif model_name == 'pvalue':
        kwargs_list = df.to_dict('records')
        for kwargs in kwargs_list:
            kwargs['gene_id'] = kwargs['gene_id'][:20]
            obj = create_model('pvalue', kwargs)
            obj.save()


def create_cells(hdf_files: List[Path]):
    for cell_file in hdf_files:
        cell_df = pd.read_hdf(cell_file, 'cell')
        if 'codex' in fspath(cell_file):
            create_proteins(cell_df)
        df_to_db(cell_df, 'cell')
    return


def create_genes(json_files: List[Path]):
    gene_list = []

    for file in json_files:
        partial_gene_dict = {}

        with open(file) as gene_dictionary:
            partial_gene_dict = json.load(gene_dictionary)

        partial_gene_list = [key[:20] for key in partial_gene_dict.keys()]
        gene_list.extend(partial_gene_list)

    gene_set = list(set(gene_list))

    save_genes(gene_set)

    return


def create_organs(hdf_files: List[Path]):
    organ_df = merge_organs(hdf_files)
    df_to_db(organ_df, 'organ')

    return


def merge_organs(hdf_files: List[Path]):
    organ_dfs = [pd.read_hdf(file, 'organ').astype(object) for file in hdf_files]
    merged_df = reduce(outer_join, organ_dfs)

    return merged_df


def create_quants(hdf_files: List[Path]):
    for file in hdf_files:
        modality = file.stem.split('_')[0]
        with pd.HDFStore(file) as store:
#            for i in range(len(store.get('quant').index) // 1000 + 1):
            for i in range(1):
                chunk = store.select('quant', start=i * 1000, stop=(i + 1) * 1000)
                df_to_db(chunk, 'quant', modality)


def create_pvals(hdf_files: List[Path]):
    for file in hdf_files:
        with pd.HDFStore(file) as store:
            if '/p_values' in store.keys():
                pval_df = store.get('p_values')
                df_to_db(pval_df, 'pvalue')


def create_modalities_and_datasets(hdf_files: List[Path]):
    for file in hdf_files:
        modality_name = file.stem
        modality = Modality(modality_name=modality_name)
        modality.save()
        with pd.HDFStore(file) as store:
            cell_df = store.get('cell')
            for uuid in cell_df['dataset'].unique():
                dataset = Dataset(uuid=uuid[:32], modality=modality)
                dataset.save()



def main(rna_directory: Path, atac_directory: Path, codex_directory: Path):
    rna_files = [file for file in rna_directory.iterdir()]
    atac_files = [file for file in atac_directory.iterdir()]
    codex_files = [file for file in codex_directory.iterdir()]

    all_files = [rna_files, atac_files, codex_files]
    modality_list = ['rna', 'atac', 'codex']

    hdf_files = [file for files in all_files for file in files if file.stem in modality_list]
    json_files = [file for files in all_files for file in files if 'json' in fspath(file)]


    create_organs(hdf_files)
    print('Organs created')
    create_modalities_and_datasets(hdf_files)
    print('Modalities and datasets created')
    create_cells(hdf_files)
    print('Cells created')
    create_genes(json_files)
    print('Genes created')
    #    create_quants(hdf_files)
    print('Quants created')
    create_pvals(hdf_files)
    print('PVals created')


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('rna_directory', type=Path)
    p.add_argument('atac_directory', type=Path)
    p.add_argument('codex_directory', type=Path)
    args = p.parse_args()

    main(args.rna_directory, args.atac_directory, args.codex_directory)
