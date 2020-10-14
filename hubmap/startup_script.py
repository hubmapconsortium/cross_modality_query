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
    CellGrouping,
    Gene,
    Protein,
    Quant,
)


def sanitize_string(string: str) -> str:
    return ''.join([char for char in string if char.isalnum() or char in '.-'])


def coalesce_organs(group_df: pd.DataFrame):
    organs_df = group_df[group_df['group_type'] == 'tissue_type']
    for organ in organs_df['group_id'].unique():
        organ_df = organs_df[organs_df['group_id'] == organ]
        cells = []
        genes = []
        marker_genes = []
        for i, row in organ_df.iterrows():
            print(type(row['cells']))
            if isinstance(row['cells'], list):
                cells.extend(row['cells'])
            elif isinstance(row['cells'], str):
                cells.extend(row['cells'].strip('[]').split(' '))
            if isinstance(row['genes'], list):
                genes.extend(row['genes'])
            elif isinstance(row['genes'], str):
                genes.extend(row['genes'].strip('[]').split(' '))
            if isinstance(row['marker_genes'], list):
                marker_genes.extend(row['marker_genes'])
            elif isinstance(row['marker_genes'], str):
                marker_genes.extend(row['marker_genes'].strip('[]').split(' '))
            cells = list(set(cells))
            genes = list(set(genes))
            marker_genes = list(set(marker_genes))

            cells = [sanitize_string(cell) for cell in cells]
            genes = [sanitize_string(gene) for gene in genes]

        group_df = group_df[group_df['group_id'] != organ].copy()
        organ_dict = {'group_type': 'tissue_type', 'group_id': organ, 'cells': cells, 'genes': genes,
                      'marker_genes': marker_genes}
        group_df = group_df.append(organ_dict, ignore_index=True)
    return group_df


def outer_join(df_1: pd.DataFrame, df_2: pd.DataFrame):
    return pd.concat([df_1, df_2], join='outer')


def create_model(model_name: str, kwargs: dict):
    if model_name == 'cell':
        obj = Cell(**kwargs)
    elif model_name == 'gene':
        obj = Gene(**kwargs)
    elif model_name == 'group':
        obj = CellGrouping(**kwargs)
    elif model_name == 'quant':
        obj = Quant(**kwargs)
    elif model_name == 'protein':
        obj = Protein(**kwargs)
    else:
        obj = None
    return obj


def sanitize_nans(kwargs: dict):
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
def save_genes(gene_set):
    for gene in gene_set:
        g = Gene(gene_symbol=gene)
        g.save()

def process_cell_records(cell_df):
    cell_fields = ['cell_id', 'tissue_type', 'dataset', 'protein_mean', 'protein_total', 'protein_covar']

    if 'cell_id' not in cell_df.columns:
        cell_df['cell_id'] = cell_df.index

    records = cell_df.to_dict('records')
    records = sanitize_nans({key: records[key] for key in records.keys() if key in cell_fields})
    for record in records:
        for key in record.keys():
            if 'protein' in key and isinstance([key], str):
                record[key] = json.loads(record[key])

    return records

@transaction.atomic
def df_to_db(df: pd.DataFrame, model_name: str, modality=None):
    group_fields = ['group_type', 'group_id']

    if model_name == 'group':

        for i, row in df.iterrows():
            if row['group_type'] == 'tissue_type':
                kwargs = {column: row[column] for column in group_fields}

                obj = create_model(model_name, kwargs)
                obj.save()

                cell_list = list(df.at[i, 'cells'])[:50]
                print(cell_list)
                cells = [Cell.objects.filter(cell_id__icontains=cell).first() for cell in cell_list]
                cells = [cell for cell in cells if cell is not None]
                print(cells)
                if len(cells) > 0:
                    obj.cells.add(*cells)

                gene_list = list(df.at[i, 'genes'])[:50]
                print(gene_list)
                genes = [Gene.objects.filter(gene_symbol__icontains=gene).first() for gene in gene_list]
                genes = [gene for gene in genes if gene is not None]
                print(genes)
                if len(genes) > 0:
                    obj.genes.add(*genes)

                marker_genes = [Gene.objects.filter(gene_symbol__icontains=gene).first() for gene in
                                list(df.at[i, 'marker_genes'])]
                marker_genes = [gene for gene in marker_genes if gene is not None]
                if len(marker_genes) > 0:
                    obj.marker_genes.add(*marker_genes)

    elif model_name == 'quant':
        dict_list = [{'cell_id': i, 'gene_id': column, 'modality': modality, 'value': df.at[i, column]} for i in df.index for column in df.columns]
        for kwargs in dict_list:
            obj = create_model('quant', kwargs)
            obj.save()

    elif model_name == 'cell':

        records = process_cell_records(df)

        for kwargs in records:
            obj = create_model('cell', kwargs)
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

    gene_set = set(gene_list)

    save_genes(gene_set)

    return


def create_groups(hdf_files: List[Path]):
    group_df = merge_groupings(hdf_files)
    group_df = coalesce_organs(group_df)
    df_to_db(group_df, 'group')

    return


def merge_groupings(group_files: List[Path]):
    group_dfs = [pd.read_hdf(group_file, 'group').astype(object) for group_file in group_files]
    merged_df = reduce(outer_join, group_dfs)

    return merged_df


def create_quants(hdf_files: List[Path]):

    for file in hdf_files:
        modality = file.stem.split('_')[0]
        with pd.HDFStore(file) as store:
            for i in range(len(store.get('quant').index) // 1000 + 1):
                chunk = store.select('quant', start=i*1000, stop=(i+1)*1000)
                df_to_db(chunk, 'quant', modality)


def main(rna_directory: Path, atac_directory: Path, codex_directory: Path):
    rna_files = [file for file in rna_directory.iterdir()]
    atac_files = [file for file in atac_directory.iterdir()]
    codex_files = [file for file in codex_directory.iterdir()]

    all_files = [rna_files, atac_files, codex_files]
    modality_list = ['rna', 'atac', 'codex']

    hdf_files = [file for files in all_files for file in files if file.stem in modality_list]
    json_files = [file for files in all_files for file in files if 'json' in fspath(file)]

    create_cells(hdf_files)
    print('Cells created')
    create_genes(json_files)
    print('Genes created')
    create_groups(hdf_files)
    print('Groups created')
    create_quants(hdf_files)
    print('Quants created')


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('rna_directory', type=Path)
    p.add_argument('atac_directory', type=Path)
    p.add_argument('codex_directory', type=Path)
    args = p.parse_args()

    main(args.rna_directory, args.atac_directory, args.codex_directory)
