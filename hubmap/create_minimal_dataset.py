#!/usr/bin/env python

from functools import reduce
from typing import List
from pathlib import Path
from os import fspath
from argparse import ArgumentParser
import pandas as pd
import json

if __name__ == '__main__':
    import django

    django.setup()


def make_mini_json_files(json_files, gene_set):
    for json_file in json_files:
        mini_gene_dict = {}
        with open(json_file, 'r') as input_file:
            input_dict = json.load(input_file)
            mini_gene_dict = {key: input_dict[key] for key in input_dict.keys() if key in gene_set}
        output_filename = 'mini_' + json_file.stem + '.json'
        with open(output_filename, 'w') as output_file:
            json.dump(mini_gene_dict, output_file)


def make_mini_group_files(group_files, cell_set, gene_set):
    for group_file in group_files:
        group_df = pd.read_csv(group_file)

        for i, row in group_df.iterrows():
            group_df.at[i, 'cells'] = [cell for cell in group_df.at[i, 'cells'][:50] if cell in cell_set]
            if 'genes' in group_df.columns:
                group_df.at[i, 'genes'] = [gene for gene in group_df.at[i, 'genes'][:50] if gene in gene_set]

        group_df.to_csv('mini_' + group_file.stem + '.csv')


def make_mini_cell_files(cell_files, cell_set):
    for cell_file in cell_files:
        cell_df = pd.read_csv(cell_file)
        if 'cell_id' not in cell_df.columns:
            cell_df['cell_id'] = cell_df.index
        cell_df = cell_df[cell_df['cell_id'] in cell_set].copy()
        cell_df.to_csv('mini_' + cell_file.stem + '.csv')


def make_mini_quant_files(quant_files, cell_set, gene_set):
    for quant_file in quant_files:
        gene_list = list(gene_set)
        quant_df = pd.read_csv(quant_file)
        quant_df = quant_df[gene_list].copy()
        if 'cell_id' not in quant_df.columns:
            quant_df['cell_id'] = quant_df.index
        quant_df = quant_df[quant_df['cell_id'] in cell_set].copy()
        quant_df.to_csv('mini_' + quant_file.stem + '.csv')


def get_cells_and_genes(group_df):
    cell_set = set({})
    gene_set = set({})
    for i, row in group_df.iterrows():
        for cell in row['cells'][:50]:
            cell_set.add(cell)
        for gene in row['genes'][:50]:
            gene_set.add(gene)
    return cell_set, gene_set


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
                cells.extend(row['cells'].split(' '))
            if isinstance(row['genes'], list):
                genes.extend(row['genes'])
            elif isinstance(row['genes'], str):
                genes.extend(row['genes'].split(' '))
            if isinstance(row['marker_genes'], list):
                marker_genes.extend(row['marker_genes'])
            elif isinstance(row['marker_genes'], str):
                marker_genes.extend(row['marker_genes'].split(' '))
            cells = list(set(cells))
            genes = list(set(genes))
            marker_genes = list(set(marker_genes))

            cells = [cell.strip(",/'") for cell in cells]
            genes = [gene.strip(",/'") for gene in genes]

        group_df = group_df[group_df['group_id'] != organ].copy()
        organ_dict = {'group_type': 'tissue_type', 'group_id': organ, 'cells': cells, 'genes': genes,
                      'marker_genes': marker_genes}
        group_df = group_df.append(organ_dict, ignore_index=True)
    return group_df


def outer_join(df_1: pd.DataFrame, df_2: pd.DataFrame):
    return pd.concat([df_1, df_2], join='outer')


def merge_groupings(group_files: List[Path]):
    group_dfs = [pd.read_csv(group_file).astype(object) for group_file in group_files]
    merged_df = reduce(outer_join, group_dfs)

    return merged_df


def main(rna_directory: Path, atac_directory: Path, codex_directory: Path):
    rna_files = [file for file in rna_directory.iterdir()]
    atac_files = [file for file in atac_directory.iterdir()]
    codex_files = [file for file in codex_directory.iterdir()]

    all_files = [rna_files, atac_files, codex_files]
    modality_list = ['rna', 'atac', 'codex']

    cell_files = [file for files in all_files for file in files if file.stem in modality_list]
    json_files = [file for files in all_files for file in files if 'json' in fspath(file)]
    group_files = [file for files in all_files for file in files if 'group' in fspath(file)]
    quant_files = [file for files in all_files for file in files if 'quant' in fspath(file)]

    group_df = merge_groupings(group_files)
    group_df = coalesce_organs(group_df)

    cell_set, gene_set = get_cells_and_genes(group_df)

    make_mini_json_files(json_files, gene_set)

    make_mini_group_files(group_files, cell_set, gene_set)

    make_mini_cell_files(cell_files, cell_set)

    make_mini_quant_files(quant_files, cell_set, gene_set)


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('rna_directory', type=Path)
    p.add_argument('atac_directory', type=Path)
    p.add_argument('codex_directory', type=Path)
    args = p.parse_args()

    main(args.rna_directory, args.atac_directory, args.codex_directory)
