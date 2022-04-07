#!/usr/bin/env python
import hashlib
import json
import pickle
from argparse import ArgumentParser
from os import fspath
from pathlib import Path
from typing import List

import anndata
import django
import numpy as np
import pandas as pd
from django.core.cache import cache
from django.db import connection, transaction

django.setup()

from query_app.models import (
    Cell,
    CellType,
    Cluster,
    Dataset,
    Gene,
    Modality,
    Organ,
    Protein,
)

# if __name__ == "__main__":
#    import django

#    django.setup()


def set_up_cell_cluster_relationships(hdf_file, new_datasets):
    if hdf_file.stem == "codex":
        store = pd.HDFStore(hdf_file, mode="r")
        for key in store.keys():
            if key in new_datasets:
                cell_df = store.get(key)
                for i in cell_df.index:
                    cell_id = cell_df["cell_id"][i]
                    cluster_ids = cell_df["clusters"][i]
                    cell = Cell.objects.filter(cell_id=cell_id).first()
                    clusters = Cluster.objects.filter(grouping_name__in=cluster_ids)
                    cell.clusters.add(clusters)

    elif hdf_file.stem in ["atac", "rna"]:
        store = pd.HDFStore(hdf_file)
        all_clusters = store.get("cluster")["grouping_name"].unique()
        cell_df = store.get("cell")
        cell_df = cell_df[cell_df["dataset"].isin(new_datasets)]
        for cluster_id in all_clusters:
            dataset = cluster_id.split()
            cell_df = cell_df["dataset"]
            cell_ids = [
                cell_df["cell_id"][i]
                for i in cell_df.index
                if cluster_id in cell_df["clusters"][i].split(",")
            ]
            cell_pks = Cell.objects.filter(cell_id__in=cell_ids).values_list("pk", flat=True)
            cluster = Cluster.objects.filter(grouping_name=cluster_id).first()
            cluster.cells.add(*cell_pks)


def sanitize_string(string: str) -> str:
    return "".join([char for char in string if char.isalnum() or char in ".-"])


def create_model(model_name: str, kwargs: dict):
    if model_name == "cell":
        obj = Cell(**kwargs)
    elif model_name == "gene":
        obj = Gene(**kwargs)
    elif model_name == "organ":
        obj = Organ(**kwargs)
    elif model_name == "protein":
        obj = Protein(**kwargs)
    elif model_name == "cluster":
        obj = Cluster(**kwargs)
    else:
        obj = None
    return obj


@transaction.atomic
def create_proteins(hdf_file):
    h5ad_file = hdf_file.parent / Path(hdf_file.stem + ".h5ad")
    adata = anndata.read(h5ad_file)
    protein_ids = [protein for protein in adata.var.index if ":" not in protein]

    proteins = [
        Protein(protein_id=protein)
        for protein in protein_ids
        if Protein.objects.filter(protein_id__iexact=protein).first() is None
    ]

    Protein.objects.bulk_create(proteins)


@transaction.atomic
def save_genes(gene_set: List[str]):
    genes = [Gene(gene_symbol=gene) for gene in gene_set]
    Gene.objects.bulk_create(genes)


def process_cell_records(cell_df: pd.DataFrame) -> List[dict]:
    if "cell_id" not in cell_df.columns:
        cell_df["cell_id"] = cell_df.index

    records = cell_df.to_dict("records")
    cell_fields = [
        "cell_id",
        "dataset",
        "modality",
        "organ",
        "cell_type",
    ]

    sanitized_records = [
        {field: record[field] for field in record if field in cell_fields} for record in records
    ]

    for record in sanitized_records:
        if None in record.values():
            print(record)
            sanitized_records.remove(record)

        if "modality" in record.keys():
            record["modality"] = Modality.objects.filter(
                modality_name__icontains=record["modality"]
            ).first()
        record["dataset"] = Dataset.objects.filter(uuid__icontains=record["dataset"]).first()
        if "modality" not in record.keys():
            record["modality"] = record["dataset"].modality
        record["organ"] = Organ.objects.filter(grouping_name__icontains=record["organ"]).first()
        record["celL_type"] = CellType.objects.filter(
            grouping_name__icontains=record["cell_type"]
        ).first()

    return sanitized_records


@transaction.atomic
def df_to_db(df: pd.DataFrame, model_name: str, modality=None, grouping_type: str = None):
    if model_name == "cell":
        kwargs_list = process_cell_records(df)
        objs = [create_model("cell", kwargs) for kwargs in kwargs_list]
        Cell.objects.bulk_create(objs)


def create_cells(hdf_file: Path, new_datasets):
    if hdf_file.stem == "codex":
        store = pd.HDFStore(hdf_file, mode="r")
        for key in store.keys():
            if key in new_datasets:
                cell_df = pd.read_hdf(hdf_file, key)
                df_to_db(cell_df, "cell")
    else:
        store = pd.HDFStore(hdf_file)
        cell_df = store.get("cell")
        cell_df = cell_df[cell_df["dataset"].isin(new_datasets)]
        df_to_db(cell_df, "cell")


def create_genes(hdf_file: Path):
    store = pd.HDFStore(hdf_file)
    pval_df = store.get("organ")
    genes_to_create = [
        sanitize_string(gene)[:64]
        for gene in pval_df["gene_id"].unique()
        if Gene.objects.filter(gene_symbol__icontains=sanitize_string(gene)[:64]).first() is None
    ]
    print(str(len(genes_to_create)) + "genes to create")
    save_genes(genes_to_create)

    return


def create_organs(hdf_file: Path):
    if hdf_file.stem == "codex":
        organs_set = set()
        store = pd.HDFStore(hdf_file, mode="r")
        for key in store.keys():
            cell_df = pd.read_hdf(hdf_file, key)
            organs_set.update(cell_df["organ"])

        organs = list(organs_set)
    else:
        store = pd.HDFStore(hdf_file)
        cell_df = store.get("cell")
        organs = list(cell_df["organ"].unique())

    for organ_name in organs:
        if Organ.objects.filter(grouping_name__icontains=organ_name).first() is None:
            organ = Organ(grouping_name=organ_name)
            organ.save()

    return


def create_cell_types(hdf_file: Path):
    if hdf_file.stem in ["codex", "atac"]:
        return

    else:
        store = pd.HDFStore(hdf_file)
        cell_df = store.get("cell")
        cell_types = cell_df["cell_type"].unique()

    for cell_type in cell_types:
        if CellType.objects.filter(grouping_name__icontains=cell_type).first() is None:
            cell_type = CellType(grouping_name=cell_type)
            cell_type.save()

    return


def create_clusters(hdf_file: Path, new_datasets):
    if hdf_file.stem in ["atac", "rna"]:
        print("True")
        cluster_method = "leiden"
        cluster_data = "UMAP"
        with pd.HDFStore(hdf_file) as store:

            cluster_df = store.get("cluster")
            for cluster in cluster_df["grouping_name"].unique():
                dataset = cluster.split("-")[-2]
                if dataset in new_datasets:
                    dset = Dataset.objects.filter(uuid__iexact=dataset).first()
                    cluster = Cluster(
                        grouping_name=cluster,
                        cluster_method=cluster_method,
                        cluster_data=cluster_data,
                        dataset=dset,
                    )
                    cluster.save()

    elif hdf_file.stem == "codex":
        store = pd.HDFStore(hdf_file, mode="r")
        for key in store.keys():
            if key in new_datasets:
                cell_df = pd.read_hdf(hdf_file, key)
                cluster_lists = cell_df["clusters"].tolist()
                cluster_set = set(
                    [cluster for cluster_list in cluster_lists for cluster in cluster_list]
                )
                cluster_set_splits = [cluster.split("-") + [cluster] for cluster in cluster_set]
                cluster_kwargs = [
                    {
                        "cluster_method": cluster_split[0],
                        "cluster_data": cluster_split[1],
                        "dataset": cluster_split[2],
                        "grouping_name": cluster_split[-1],
                    }
                    for cluster_split in cluster_set_splits
                ]
                for cluster_kwarg_set in cluster_kwargs:
                    cluster_kwarg_set["dataset"] = Dataset.objects.filter(
                        uuid=cluster_kwarg_set["dataset"]
                    ).first()

                objs = [create_model("cluster", kwargs) for kwargs in cluster_kwargs]
                Cluster.objects.bulk_create(objs)

        return


def create_modality_and_datasets(hdf_file: Path, new_datasets):
    modality_name = hdf_file.stem
    modality = Modality.objects.filter(modality_name__iexact=modality_name).first()
    if modality is None:
        modality = Modality(modality_name=modality_name)
        modality.save()

    if modality_name == "codex":
        store = pd.HDFStore(hdf_file, mode="r")
        for key in store.keys():
            cell_df = store.get(key)
            for uuid in cell_df["dataset"].unique():
                if uuid in new_datasets:
                    dataset = Dataset(uuid=uuid[:32], modality=modality)
                    dataset.save()

    else:
        with pd.HDFStore(hdf_file) as store:
            cell_df = store.get("cell")
            for uuid in cell_df["dataset"].unique():
                if uuid in new_datasets:
                    dataset = Dataset(uuid=uuid[:32], modality=modality)
                    dataset.save()


def delete_old_data(hdf_file):
    store = pd.HDFStore(hdf_file)
    modality = hdf_file.stem
    if "/cell" in store.keys():
        new_datasets = set(store.get("cell")["dataset"].unique())
    old_datasets = Dataset.objects.filter(modality__modality_name__icontains=modality).exclude(
        uuid__in=new_datasets
    )
    old_datasets.delete()  # This should cascade
    return new_datasets


def load_data(hdf_file: Path):
    new_datasets, store = delete_old_data(hdf_file)

    print("Old data deleted")
    create_modality_and_datasets(hdf_file, new_datasets)
    print("Modality and datasets created")
    create_organs(hdf_file)
    print("Organs created")
    create_cell_types(hdf_file)
    print("Cell types created")
    create_clusters(hdf_file, new_datasets)
    print("Clusters created")
    create_cells(hdf_file, new_datasets)
    print("Cells created")
    set_up_cell_cluster_relationships(hdf_file, new_datasets)
    print("Cell cluster relationships established")
    if hdf_file.stem in ["atac", "rna"]:
        create_genes(hdf_file)
        print("Genes created")
    elif hdf_file.stem in ["codex"]:
        create_proteins(hdf_file)
        print("Proteins created")
    return


def main(hdf_files: List[Path]):
    for file in hdf_files:
        if file.stem in ["rna", "atac", "codex"]:
            load_data(file)
            print(f"{file.stem} loaded")


if __name__ == "__main__":
    import django

    django.setup()

    p = ArgumentParser()
    p.add_argument("hdf_files", type=Path, nargs="+")
    args = p.parse_args()

    main(args.hdf_files)
