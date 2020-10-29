#!/usr/bin/env python

from typing import List
from pathlib import Path
from argparse import ArgumentParser
import pandas as pd
import json
import numpy as np
from django.db import transaction, connection
import concurrent.futures

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
    RnaQuant,
    AtacQuant,
)

def get_zero_cells(quant_df, modality):
    for gene in quant_df.columns:
        gene_df = quant_df[quant_df[gene] == 0.0].copy()
        cell_ids = [cell_id for cell_id in gene_df.index]
        gene_object = Gene.objects.filter(gene_symbol__icontains=sanitize_string(gene)[:20]).first()
        cells = Cell.objects.filter(cell_id__in=cell_ids)
        cells = [cell for cell in cells]
        if modality == 'rna':
            gene_object.rna_zero_cells.add(*cells)
        elif modality == 'atac':
            gene_object.atac_zero_cells.add(*cells)

def create_quant_index(modality:str):
    sql = "CREATE INDEX " + modality + "_value_idx ON query_app_" + modality + "quant (value);"
    with connection.cursor() as cursor:
        cursor.execute(sql)

def drop_quant_index(modality:str):
    sql = 'DROP INDEX IF EXISTS ' + modality + '_value_idx;'
    with connection.cursor() as cursor:
        cursor.execute(sql)

def process_quant_column(quant_df_and_column):
    quant_df = quant_df_and_column[0]
    column = quant_df_and_column[1]

    return [{'cell_id': i, 'gene_id': column, 'value': quant_df.at[i, column]} for i in
                 quant_df.index if quant_df.at[i, column] > 0.0]

def flatten_quant_df(quant_df, modality):
    get_zero_cells(quant_df, modality)

    dict_list = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:

        df_and_columns = [(quant_df, column) for column in quant_df.columns]

        for column_list in executor.map(process_quant_column, df_and_columns):
            dict_list.extend(column_list)

    return dict_list


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
    if model_name == 'quant':
        dict_list = flatten_quant_df(df, modality)
        for kwargs in dict_list:
            cell = Cell.objects.filter(cell_id__icontains=kwargs['cell_id']).first()
            kwargs['quant_cell'] = cell
            kwargs.pop('cell_id')
            gene = Gene.objects.filter(gene_symbol__iexact=kwargs['gene_id']).first()
            kwargs['quant_gene'] = gene
            kwargs.pop('gene_id')
            if modality == 'rna':
                obj = RnaQuant(**kwargs)
            elif modality == 'atac':
                obj = AtacQuant(**kwargs)
            obj.save()

    elif model_name == 'cell':

        kwargs_list = process_cell_records(df)

        for kwargs in kwargs_list:
            obj = create_model('cell', kwargs)
            obj.save()

    elif model_name == 'pvalue':
        kwargs_list = df.to_dict('records')
        for kwargs in kwargs_list:
            kwargs['p_gene'] = Gene.objects.filter(gene_symbol__iexact=sanitize_string(kwargs['gene_id'])[:20]).first()
            kwargs.pop('gene_id')
            kwargs['p_organ'] = Organ.objects.filter(organ_name__iexact=kwargs['organ_name']).first()
            kwargs.pop('organ_name')
            kwargs['modality'] = Modality.objects.filter(modality_name__icontains=modality).first()
            obj = create_model('pvalue', kwargs)
            obj.save()


def create_cells(hdf_file: Path):
    cell_df = pd.read_hdf(hdf_file, 'cell')
    df_to_db(cell_df, 'cell')


def create_genes(hdf_file: Path):
    quant_df = pd.read_hdf(hdf_file, 'quant')
    genes_to_create = [sanitize_string(gene)[:20] for gene in quant_df.columns if
                       Gene.objects.filter(gene_symbol__icontains=sanitize_string(gene)[:20]).first() is None]
    save_genes(genes_to_create)

    return


def create_organs(hdf_file: Path):

    cell_df = pd.read_hdf(hdf_file, 'cell')
    if 'tissue_type' in cell_df.columns:
        organs = list(cell_df['tissue_type'].unique())
    elif 'organ_name' in cell_df.columns:
        organs = list(cell_df['tissue_type'].unique())

    for organ_name in organs:
        if Organ.objects.filter(organ_name__icontains=organ_name).first() is None:
            organ = Organ(organ_name=organ_name)
            organ.save()

    return


def create_quants(hdf_file: Path):
    modality = hdf_file.stem
    with pd.HDFStore(hdf_file) as store:
        chunks = len(store.get('quant').index) // 1000 + 1
        for i in range(chunks):
            print('Loading chunk ' + str(i) + ' out of ' + str(chunks))
            chunk = store.select('quant', start=i * 1000, stop=(i + 1) * 1000)
            df_to_db(chunk, 'quant', modality)


def create_pvals(hdf_file: Path):
    modality = hdf_file.stem
    with pd.HDFStore(hdf_file) as store:
        pval_df = store.get('p_values')
        df_to_db(pval_df, 'pvalue', modality)


def create_modality_and_datasets(hdf_file: Path):
    modality_name = hdf_file.stem
    modality = Modality(modality_name=modality_name)
    modality.save()
    with pd.HDFStore(hdf_file) as store:
        cell_df = store.get('cell')
        for uuid in cell_df['dataset'].unique():
            dataset = Dataset(uuid=uuid[:32], modality=modality)
            dataset.save()


def load_rna(hdf_file: Path):

    drop_quant_index('rna')
    print('Old index dropped')

    Cell.objects.filter(modality__modality_name__icontains='rna').delete()
    RnaQuant.objects.all().delete()
    Dataset.objects.filter(modality__modality_name__icontains='rna').delete()
    Modality.objects.filter(modality_name__icontains='rna').delete()

    print('Old data deleted')
    create_modality_and_datasets(hdf_file)
    print('Modality and datasets created')
    create_organs(hdf_file)
    print('Organs created')
    create_cells(hdf_file)
    print('Cells created')
    create_genes(hdf_file)
    print('Genes created')
    create_quants(hdf_file)
    print('Quants created')
    create_pvals(hdf_file)
    print('Pvals created')

    create_quant_index('rna')
    print('New index created')

    return


def load_atac(hdf_file):

    drop_quant_index('atac')
    print('Old index dropped')

    Cell.objects.filter(modality__modality_name__icontains='atac').delete()
    AtacQuant.objects.all().delete()
    Dataset.objects.filter(modality__modality_name__icontains='atac').delete()
    Modality.objects.filter(modality_name__icontains='atac').delete()

    print('Old data deleted')
    create_modality_and_datasets(hdf_file)
    print('Modality and datasets created')
    create_organs(hdf_file)
    print('Organs created')
    create_cells(hdf_file)
    print('Cells created')
    create_genes(hdf_file)
    print('Genes created')
    create_quants(hdf_file)
    print('Quants created')
    create_pvals(hdf_file)
    print('Pvals created')

    create_quant_index('atac')
    print('New index created')

    return


def load_codex(hdf_file):
    Cell.objects.filter(modality__modality_name__icontains='codex').delete()
    Dataset.objects.filter(modality__modality_name__icontains='codex').delete()
    Modality.objects.filter(modality_name__icontains='codex').delete()
    Protein.objects.all().delete()

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



if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('hdf_files', type=Path, nargs='+')
    args = p.parse_args()

    main(args.hdf_files)
