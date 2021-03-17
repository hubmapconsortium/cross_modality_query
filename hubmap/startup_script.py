#!/usr/bin/env python

import json
from argparse import ArgumentParser
from os import fspath
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from django.core.cache import cache
from django.db import connection, transaction

if __name__ == "__main__":
    import django

    django.setup()

from query_app.models import (
    AtacQuant,
    Cell,
    Cluster,
    Dataset,
    Gene,
    Modality,
    Organ,
    Protein,
    PVal,
    RnaQuant,
)


def set_up_cell_cluster_relationships(hdf_file):
    if hdf_file.stem == "codex":
        cell_df = pd.read_hdf(hdf_file, "cell")
        for i in cell_df.index:
            cell_id = cell_df["cell_id"][i]
            cluster_ids = cell_df["clusters"][i]
            cell = Cell.objects.filter(cell_id=cell_id).first()
            clusters = Cluster.objects.filter(grouping_name__in=cluster_ids)
            cell.clusters.add(clusters)

    elif hdf_file.stem in ["atac", "rna"]:
        all_clusters = pd.read_hdf(hdf_file, "cluster")["grouping_name"].unique()
        cell_df = pd.read_hdf(hdf_file, "cell")
        for cluster in all_clusters:
            cell_ids = [
                cell_df["cell_id"][i]
                for i in cell_df.index
                if cluster in cell_df["clusters"][i].split(",")
            ]
            cell_pks = Cell.objects.filter(cell_id__in=cell_ids).values_list("pk", flat=True)
            cluster.cells.add(*cell_pks)


def make_quants_csv(hdf_file):
    modality = hdf_file.stem

    csv_file = hdf_file.parent / Path(modality + ".csv")

    drop_quant_index(modality)

    if modality in ["atac", "rna"]:
        sql = (
            "COPY query_app_"
            + modality
            + "quant(id, q_cell_id, q_var_id, value)  FROM '"
            + fspath(csv_file)
            + "' CSV HEADER;"
        )

    else:
        sql = (
            "COPY query_app_"
            + modality
            + "quant(id, q_var_id, q_cell_id, statistic, value)  FROM '"
            + fspath(csv_file)
            + "' CSV HEADER;"
        )

    with connection.cursor() as cursor:
        cursor.execute(sql)

    create_quant_index(modality)


def create_quant_index(modality: str):
    sql = "CREATE INDEX " + modality + "_value_idx ON query_app_" + modality + "quant (value);"
    with connection.cursor() as cursor:
        cursor.execute(sql)


def drop_quant_index(modality: str):
    sql = "DROP INDEX IF EXISTS " + modality + "_value_idx;"
    with connection.cursor() as cursor:
        cursor.execute(sql)


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
    elif model_name == "pvalue":
        obj = PVal(**kwargs)
    elif model_name == "cluster":
        obj = Cluster(**kwargs)
    else:
        obj = None
    return obj


@transaction.atomic
def create_proteins(hdf_file):
    csv_file = hdf_file.parent / Path(hdf_file.stem + ".csv")
    quant_df = pd.read_csv(csv_file)
    protein_ids = [protein for protein in quant_df["q_var_id"].unique() if ":" not in protein]

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

    return sanitized_records


def process_pval_args(kwargs: dict, modality: str, grouping_type: str):
    kwargs["p_gene"] = Gene.objects.filter(
        gene_symbol__iexact=sanitize_string(kwargs["gene_id"])[:64]
    ).first()
    kwargs.pop("gene_id")

    if grouping_type == "organ":
        kwargs["p_organ"] = Organ.objects.filter(
            grouping_name__iexact=kwargs["grouping_type"]
        ).first()

    elif grouping_type == "cluster":
        kwargs["p_cluster"] = Cluster.objects.filter(
            grouping_name__iexact=kwargs["grouping_type"]
        ).first()

    kwargs.pop("grouping_type")

    kwargs["modality"] = Modality.objects.filter(modality_name__icontains=modality).first()
    return kwargs


@transaction.atomic
def df_to_db(df: pd.DataFrame, model_name: str, modality=None, grouping_type: str = None):
    if model_name == "cell":

        kwargs_list = process_cell_records(df)
        objs = [create_model("cell", kwargs) for kwargs in kwargs_list]
        Cell.objects.bulk_create(objs)

        ids_list = Cell.objects.filter(modality__modality_name__iexact=modality).values_list(
            "id", "cell_id"
        )
        ids_dict = {id[1]: id[0] for id in ids_list}
        cache.set_many(ids_dict, None)

    elif model_name == "pvalue":
        kwargs_list = df.to_dict("records")
        processed_kwargs_list = [
            process_pval_args(kwargs, modality, grouping_type) for kwargs in kwargs_list
        ]
        objs = [create_model("pvalue", kwargs) for kwargs in processed_kwargs_list]
        PVal.objects.bulk_create(objs)


def create_cells(hdf_file: Path):
    cell_df = pd.read_hdf(hdf_file, "cell")

    df_to_db(cell_df, "cell")


def create_genes(hdf_file: Path):
    pval_df = pd.read_hdf(hdf_file, "organ")
    genes_to_create = [
        sanitize_string(gene)[:64]
        for gene in pval_df["gene_id"].unique()
        if Gene.objects.filter(gene_symbol__icontains=sanitize_string(gene)[:64]).first() is None
    ]
    print(str(len(genes_to_create)) + "genes to create")
    save_genes(genes_to_create)

    return


def create_organs(hdf_file: Path):
    cell_df = pd.read_hdf(hdf_file, "cell")
    organs = list(cell_df["organ"].unique())

    for organ_name in organs:
        if Organ.objects.filter(grouping_name__icontains=organ_name).first() is None:
            organ = Organ(grouping_name=organ_name)
            organ.save()

    return


def create_pvals(hdf_file: Path):
    modality = hdf_file.stem

    for grouping_type in ["organ", "cluster"]:
        with pd.HDFStore(hdf_file) as store:
            pval_df = store.get(grouping_type)
            df_to_db(pval_df, "pvalue", modality, grouping_type)


def create_clusters(hdf_file: Path):

    if hdf_file.stem in ["atac", "rna"]:
        print("True")
        cluster_method = "leiden"
        cluster_data = "UMAP"
        with pd.HDFStore(hdf_file) as store:

            cluster_df = store.get("cluster")
            for cluster in cluster_df["grouping_name"].unique():
                dataset = cluster.split("-")[-2]
                dset = Dataset.objects.filter(uuid__iexact=dataset).first()
                cluster = Cluster(
                    grouping_name=cluster,
                    cluster_method=cluster_method,
                    cluster_data=cluster_data,
                    dataset=dset,
                )

    elif hdf_file.stem == "codex":
        cell_df = pd.read_hdf(hdf_file, "cell")
        cluster_lists = cell_df["clusters"].tolist()
        cluster_set = set([cluster for cluster_list in cluster_lists for cluster in cluster_list])
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


def create_modality_and_datasets(hdf_file: Path):
    modality_name = hdf_file.stem
    modality = Modality.objects.filter(modality_name__iexact=modality_name).first()
    if modality is None:
        modality = Modality(modality_name=modality_name)
        modality.save()
    with pd.HDFStore(hdf_file) as store:
        cell_df = store.get("cell")
        for uuid in cell_df["dataset"].unique():
            dataset = Dataset(uuid=uuid[:32], modality=modality)
            dataset.save()


def delete_old_data(modality: str):
    Cell.objects.filter(modality__modality_name__icontains=modality).delete()
    modality_datasets = Dataset.objects.filter(
        modality__modality_name__icontains=modality
    ).values_list("pk", flat=True)
    Dataset.objects.filter(modality__modality_name__icontains="rna").delete()
    Cluster.objects.filter(dataset__in=modality_datasets).delete()
    Modality.objects.filter(modality_name__icontains=modality).delete()

    if modality in ["atac", "rna"]:
        PVal.objects.filter(modality__modality_name__icontains=modality).delete()
        if modality == "atac":
            AtacQuant.objects.all().delete()
        elif modality == "rna":
            RnaQuant.objects.all().delete()
    elif modality in ["codex"]:
        Protein.objects.all().delete()


def load_data(hdf_file: Path):
    delete_old_data(hdf_file.stem)

    print("Old data deleted")
    create_modality_and_datasets(hdf_file)
    print("Modality and datasets created")
    create_organs(hdf_file)
    print("Organs created")
    create_clusters(hdf_file)
    print("Clusters created")
    create_cells(hdf_file)
    print("Cells created")
    set_up_cell_cluster_relationships(hdf_file)
    print("Cell cluster relationships established")
    make_quants_csv(hdf_file)
    print("Quants created")
    if hdf_file.stem in ["atac", "rna"]:
        create_genes(hdf_file)
        print("Genes created")
        create_pvals(hdf_file)
        print("Pvals created")
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
    p = ArgumentParser()
    p.add_argument("hdf_files", type=Path, nargs="+")
    args = p.parse_args()

    main(args.hdf_files)
