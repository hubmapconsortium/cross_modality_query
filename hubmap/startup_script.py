#!/usr/bin/env python

from typing import List
from pathlib import Path
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
        modality = Modality.objects.filter(modality_name__icontains=modality).first()
        dict_list = [{'cell_id': i, 'gene_id': column, 'modality': modality, 'value': df.at[i, column]} for i in
                     df.index for column in df.columns]
        for kwargs in dict_list:
            cell = Cell.objects.filter(cell_id__icontains=kwargs['cell_id']).first()
            kwargs['quant_cell'] = cell
            kwargs.pop('cell_id')
            gene = Gene.objects.filter(gene_id__iexact=kwargs['gene_id'].first())
            kwargs['quant_gene'] = gene
            kwargs.pop('gene_id')
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
    pval_df = pd.read_hdf(hdf_file, 'p_values')
    for organ_name in pval_df['organ_name'].unique():
        if Organ.objects.filter(organ_name__icontains=organ_name).first() is None:
            organ = Organ(organ_name=organ_name)
            organ.save()

    return


def create_quants(hdf_file: Path):
    modality = hdf_file.stem
    with pd.HDFStore(hdf_file) as store:
        #            for i in range(len(store.get('quant').index) // 1000 + 1):
        for i in range(1):
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
    Cell.objects.filter(modality__modality_name__icontains='rna').delete()
    Quant.objects.filter(modality__modality_name__icontains='rna').delete()
    Dataset.objects.filter(modality__modality_name__icontains='rna').delete()
    Modality.objects.filter(modality_name__icontains='rna').delete()

    create_modality_and_datasets(hdf_file)
    create_organs(hdf_file)
    create_cells(hdf_file)
    create_genes(hdf_file)
    create_quants(hdf_file)
    create_pvals(hdf_file)

    return


def load_atac(hdf_file):
    Cell.objects.filter(modality__modality_name__icontains='atac').delete()
    Quant.objects.filter(modality__modality_name__icontains='atac').delete()
    Dataset.objects.filter(modality__modality_name__icontains='atac').delete()
    Modality.objects.filter(modality_name__icontains='atac').delete()

    create_modality_and_datasets(hdf_file)
    create_organs(hdf_file)
    create_cells(hdf_file)
    create_genes(hdf_file)
    create_quants(hdf_file)
    create_pvals(hdf_file)

    return


def load_codex(hdf_file):
    Cell.objects.filter(modality__modality_name__icontains='codex').delete()
    Quant.objects.filter(modality__modality_name__icontains='codex').delete()
    Dataset.objects.filter(modality__modality_name__icontains='codex').delete()
    Modality.objects.filter(modality_name__icontains='codex').delete()
    Protein.objects.all().delete()

    create_modality_and_datasets(hdf_file)
    create_organs(hdf_file)
    create_cells(hdf_file)
    create_proteins(hdf_file)

    return


def main(hdf_files: List[Path]):
    print(Gene.objects.all().values_list())
    print(Cell.objects.all().values_list())
    print(Organ.objects.all().values_list())

    Cell.objects.all().delete()
    Organ.objects.all().delete()
    Gene.objects.all().delete()
    PVal.objects.all().delete()
    Quant.objects.all().delete()

    rna = Modality.objects.filter(modality_name__icontains='rna').first()

    best1 = Gene(gene_symbol='BEST1')
    best1.save()
    b2m = Gene(gene_symbol='B2M')
    b2m.save()

    spleen = Organ(organ_name='spleen')
    spleen.save()
    kidney = Organ(organ_name='kidney')
    kidney.save()

    cell_one = Cell(cell_id='cell_1', modality=rna, organ=spleen, protein_mean={'Ki67':10.0, 'CD21':5.0})
    cell_one.save()
    cell_two = Cell(cell_id='cell_2', modality=rna, organ=kidney, protein_mean={'Ki67':10.0, 'CD21':0.0})
    cell_two.save()

    pval_one = PVal(p_gene=best1, p_organ=kidney, modality=rna, value=0.01)
    pval_one.save()
    pval_two = PVal(p_gene=b2m, p_organ=kidney, modality=rna, value=0.01)
    pval_two.save()
    pval_three = PVal(p_gene=best1, p_organ=spleen, modality=rna, value=0.01)
    pval_three.save()
    pval_four = PVal(p_gene=b2m, p_organ=kidney, modality=rna, value=1.00)
    pval_four.save()

    quant_one = Quant(quant_cell=cell_one, quant_gene=best1, modality=rna, value=10.1)
    quant_one.save()
    quant_two = Quant(quant_cell=cell_one, quant_gene=b2m, modality=rna, value=10.1)
    quant_two.save()
    quant_three = Quant(quant_cell=cell_two, quant_gene=best1, modality=rna, value=10.1)
    quant_three.save()
    quant_four = Quant(quant_cell=cell_two, quant_gene=b2m, modality=rna, value=0.0)
    quant_four.save()

#    new_index = False

#    if Quant.objects.count() > 0:
#        for file in hdf_files:
#            if file.stem in ['atac', 'rna']:
                #Delete index
#                new_index=True
#                break

#    for file in hdf_files:
#        if 'rna' in file.stem:
#            load_rna(file)
#        elif 'atac' in file.stem:
#            load_atac(file)
#        elif 'codex' in file.stem:
#            load_codex(file)



if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('hdf_files', type=Path, nargs='+')
    args = p.parse_args()

    main(args.hdf_files)
