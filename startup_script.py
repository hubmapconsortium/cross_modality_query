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
    RnaQuant,
    AtacQuant,
)


def outer_join(df_1: pd.DataFrame, df_2: pd.DataFrame):
    return pd.concat([df_1, df_2], join='outer')


def create_model(model_name: str, kwargs: dict):
    if model_name == 'cell':
        obj = Cell(**kwargs)
    elif model_name == 'gene':
        obj = Gene(**kwargs)
    elif model_name == 'group':
        obj = CellGrouping(**kwargs)
    elif model_name == 'rna_quant':
        obj = RnaQuant(**kwargs)
    elif model_name == 'atac_quant':
        obj = AtacQuant(**kwargs)
    else:
        obj = None
    return obj


def sanitize_nans(kwargs):
    for key in kwargs.keys():
        if type(kwargs[key]) == float and np.isnan(kwargs[key]):
            kwargs[key] = {}

    return kwargs


@transaction.atomic
def save_genes(gene_set):
    for gene in gene_set:
        g = Gene(gene_symbol=gene)
        g.save()


@transaction.atomic
def df_to_db(df: pd.DataFrame, model_name: str):
    group_fields = ['group_type', 'group_id']

    if model_name == 'group':

        for i, row in df.iterrows():
            kwargs = {column: row[column] for column in group_fields}

            obj = create_model(model_name, kwargs)
            obj.save()

            cells = [Cell.objects.filter(cell_id__icontains=cell).first() for cell in list(df.at[i, 'cells'])]
            cells = [cell for cell in cells if cell is not None]
            if len(cells) > 0:
                obj.cells.add(cells)

            genes = [Gene.objects.filter(gene_symbol__icontains=gene).first() for gene in list(row['genes'])]
            genes = [gene for gene in genes if gene is not None]
            obj.genes.add(genes)

            marker_genes = [Gene.objects.filter(gene_symbol__icontains=gene).first() for gene in
                            list(row['marker_genes'])]
            marker_genes = [gene for gene in marker_genes if gene is not None]
            obj.marker_genes.add(marker_genes)


    else:

        for i, row in df.iterrows():
            kwargs = {column: row[column] for column in df.columns}
            kwargs = sanitize_nans(kwargs)
            for key in kwargs.keys():
                if 'protein' in key and isinstance(kwargs[key], str):
                    kwargs[key] = json.loads(kwargs[key])
            obj = create_model(model_name, kwargs)
            obj.save()


def create_cells(cell_files: List[Path]):
    cell_df, quant_dfs = merge_cells(cell_files)

    df_to_db(cell_df, 'cell')
    df_to_db(quant_dfs['rna'], 'rna_quant')
    df_to_db(quant_dfs['atac'], 'atac_quant')

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


def create_groups(group_files: List[Path]):
    group_df = merge_groupings(group_files)
    df_to_db(group_df, 'group')

    return


def merge_cells(cell_files: List[Path]):
    keep_columns = ['cell_id', 'modality', 'protein_mean', 'protein_total', 'protein_covar']
    cell_dfs = [pd.read_csv(cell_file) for cell_file in cell_files]
    quant_dfs = {}

    for cell_df in cell_dfs:
        if 'atac' in cell_df['modality'].tolist():
            quant_dfs['atac'] = populate_quant_tables(cell_df, 'atac')
        elif 'rna' in cell_df['modality'].tolist():
            quant_dfs['rna'] = populate_quant_tables(cell_df, 'rna')

    merged_df = reduce(outer_join, cell_dfs)
    merged_df = merged_df[keep_columns].copy()

    return merged_df, quant_dfs


def merge_groupings(group_files: List[Path]):
    group_dfs = [pd.read_csv(group_file).astype(object) for group_file in group_files]
    merged_df = reduce(outer_join, group_dfs)

    return merged_df


def populate_quant_tables(cell_df: pd.DataFrame, modality: str):
    quant_df = cell_df.select_dtypes(np.number)

    # make sure index is cell_id here
    dict_list = [{'cell_id': i, 'gene_id': column, 'value': quant_df.at[i, column]} for i in quant_df.index for column
                 in quant_df.columns]

    new_quant_df = pd.DataFrame(dict_list)
    return new_quant_df


def main(rna_directory: Path, atac_directory: Path, codex_directory: Path):
    rna_files = [file for file in rna_directory.iterdir()]
    atac_files = [file for file in atac_directory.iterdir()]
    codex_files = [file for file in codex_directory.iterdir()]

    all_files = [rna_files, atac_files, codex_files]
    modality_list = ['rna', 'atac', 'codex']

    cell_files = [file for files in all_files for file in files if file.stem in modality_list]
    json_files = [file for files in all_files for file in files if 'json' in fspath(file)]
    group_files = [file for files in all_files for file in files if 'group' in fspath(file)]

    #    create_cells(cell_files)
    #    create_genes(json_files)
    create_groups(group_files)


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('rna_directory', type=Path)
    p.add_argument('atac_directory', type=Path)
    p.add_argument('codex_directory', type=Path)
    args = p.parse_args()

    main(args.rna_directory, args.atac_directory, args.codex_directory)
