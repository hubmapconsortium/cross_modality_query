import hashlib
import pickle
from datetime import datetime
from os import fspath
from pathlib import Path

import anndata
import pandas as pd
import zarr
from django.apps import AppConfig
from django.conf import settings
from django.db.utils import ProgrammingError
from pymongo import MongoClient
from tables.exceptions import HDF5ExtError
from zarr.errors import PathNotFoundError

PATH_TO_H5AD_FILES = Path("/opt")
PATH_TO_CODEX_H5AD = PATH_TO_H5AD_FILES / "codex.h5ad"
PATH_TO_RNA_H5AD = PATH_TO_H5AD_FILES / "rna.h5ad"
PATH_TO_ATAC_H5AD = PATH_TO_H5AD_FILES / "atac.h5ad"
PATH_TO_RNA_PVALS = PATH_TO_H5AD_FILES / "rna.hdf5"
PATH_TO_ATAC_PVALS = PATH_TO_H5AD_FILES / "atac.hdf5"
PATH_TO_CODEX_PVALS = PATH_TO_H5AD_FILES / "codex.hdf5"
PATH_TO_RNA_PERCENTAGES = PATH_TO_H5AD_FILES / "rna_precompute.hdf5"
PATH_TO_ATAC_PERCENTAGES = PATH_TO_H5AD_FILES / "atac_precompute.hdf5"
PATH_TO_CODEX_PERCENTAGES = PATH_TO_H5AD_FILES / "codex_precompute.hdf5"


def make_pickle_and_hash(qs, set_type):
    client = MongoClient(settings.MONGO_HOST_AND_PORT)
    collection = client[settings.MONGO_DB_NAME][settings.MONGO_COLLECTION_NAME]

    qry = qs.query
    query_pickle = pickle.dumps(qry)
    query_handle = str(hashlib.sha256(query_pickle).hexdigest())

    doc = {
        "query_handle": query_handle,
        "query_pickle": query_pickle,
        "set_type": set_type,
        "created_at": datetime.utcnow(),
    }
    collection.insert_one(doc)

    return query_handle


def set_up_mongo():
    print(settings.MONGO_HOST_AND_PORT)
    client = MongoClient(settings.MONGO_HOST_AND_PORT)
    db = client[settings.MONGO_DB_NAME][settings.MONGO_COLLECTION_NAME]
    db.create_index("created_at", expireAfterSeconds=settings.TOKEN_EXPIRATION_TIME)
    #    db.log_events.createIndex({"created_at": 1}, {expireAfterSeconds: TOKEN_EXPIRATION_TIME})


def compute_dataset_hashes():
    from .models import Cell, Dataset, Modality

    hash_dict = {}
    uuid_dict = {}
    count_dict = {}
    try:
        for uuid in Dataset.objects.all().values_list("uuid", flat=True):
            print(uuid)
            query_set = Cell.objects.filter(dataset__uuid__in=[uuid]).distinct("cell_id")
            print(query_set.query)
            hash = make_pickle_and_hash(query_set, "cell")
            print(hash)
            hash_dict[hash] = uuid
            uuid_dict[uuid] = hash
            count_dict[hash] = query_set.count()

        for modality in Modality.objects.all().values_list("modality_name", flat=True):
            print(modality)
            query_set = Cell.objects.filter(modality__modality_name__in=[modality]).distinct(
                "cell_id"
            )
            print(query_set.query)
            hash = make_pickle_and_hash(query_set, "cell")
            print(hash)
            hash_dict[hash] = modality
            uuid_dict[modality] = hash
            count_dict[hash] = query_set.count()
    except ProgrammingError:
        # empty database, most likely
        pass
    return hash_dict, uuid_dict, count_dict


def get_pval_df(path_to_pvals):
    with pd.HDFStore(path_to_pvals) as store:
        grouping_keys = ["organ", "cluster"]
        grouping_dfs = [store.get(key) for key in grouping_keys]
        return pd.concat(grouping_dfs)


def attempt_to_open_file(file_path, key=None):
    if key is None:
        assert file_path.suffix == ".h5ad"
        try:
            adata = anndata.read(file_path)
            adata.var_names_make_unique()
        except FileNotFoundError:
            print(f"File path: {file_path} not found")
            adata = anndata.AnnData()
        return adata

    elif key in {"cell", "percentages"}:
        assert file_path.suffix == ".hdf5"
        try:
            if file_path.stem == "codex" and key == "cell":
                store = pd.HDFStore(file_path)
                dfs = [store.get(key) for key in store.keys()]
                df = pd.concat(dfs)

            else:
                df = pd.read_hdf(file_path, key)

            columns_dict = {"percentages": ["var_id", "cutoff", "dataset"], "cell": ["dataset"]}

            if key == "cell":
                if "cell_type" not in df.columns:
                    df["cell_type"] = "unknown"

                if "clusters" in df.columns:
                    df = df[~df["clusters"].isna()]

                    if isinstance(df["clusters"].iloc[0], str):
                        df["clusters"] = df["clusters"].str.split(",")

                    old_clusters_list = df["clusters"].to_list()
                    cell_types_list = df["cell_type"].to_list()
                    new_clusters_list = [old_clusters_list[i] + [cell_types_list[i]] for i in range(len(old_clusters_list))]
                    df["clusters"] = pd.Series(new_clusters_list, index=df.index)

            df = df.set_index(columns_dict[key], drop=False, inplace=False).sort_index()

        except (FileNotFoundError, KeyError, ValueError, HDF5ExtError):
            print(f"File path: {file_path} not found")
            columns_dict = {
                "percentages": ["var_id", "cutoff", "dataset", "percentage"],
                "cell": ["cell_id", "dataset", "organ", "modality", "clusters"],
            }
            df = pd.DataFrame(columns=columns_dict[key])

        return df

    elif key == "pval":
        assert file_path.suffix == ".hdf5"
        try:
            df = get_pval_df(file_path)
        except (FileNotFoundError, KeyError, HDF5ExtError):
            print(f"File path: {file_path} not found")
            df = pd.DataFrame(columns=["grouping_name", "gene_id", "value"])
        return df


class QueryAppConfig(AppConfig):
    name = "query_app"

    def ready(self):
        global codex_adata
        global rna_adata
        global atac_adata
        global rna_pvals
        global atac_pvals
        global rna_percentages
        global atac_percentages
        global codex_percentages
        global codex_cell_df
        global rna_cell_df
        global atac_cell_df
        global hash_dict
        global uuid_dict
        global count_dict
        global zarr_root
        global codex_store

        set_up_mongo()

        codex_adata = attempt_to_open_file(PATH_TO_CODEX_H5AD)
        rna_adata = attempt_to_open_file(PATH_TO_RNA_H5AD)
        atac_adata = attempt_to_open_file(PATH_TO_ATAC_H5AD)

        hash_dict, uuid_dict, count_dict = compute_dataset_hashes()

        print("Quant adatas read in")
        if settings.SKIP_LOADING_PVALUES:
            atac_pvals = pd.DataFrame()
            rna_pvals = pd.DataFrame()
        else:
            rna_pvals = attempt_to_open_file(PATH_TO_RNA_PVALS, "pval")
            atac_pvals = attempt_to_open_file(PATH_TO_ATAC_PVALS, "pval")
        print("Pvals read in")
        rna_percentages = attempt_to_open_file(PATH_TO_RNA_PERCENTAGES, "percentages")
        atac_percentages = attempt_to_open_file(PATH_TO_ATAC_PERCENTAGES, "percentages")
        codex_percentages = attempt_to_open_file(PATH_TO_CODEX_PERCENTAGES, "percentages")
        print("Percentages read in")
        rna_cell_df = attempt_to_open_file(PATH_TO_RNA_PVALS, "cell")
        atac_cell_df = attempt_to_open_file(PATH_TO_ATAC_PVALS, "cell")
        codex_cell_df = attempt_to_open_file(PATH_TO_CODEX_PVALS, "cell")
        try:
            zarr_root = zarr.open("/opt/data/zarr/example.zarr", mode="r")
        except PathNotFoundError:
            zarr_root = zarr.open("/opt/data/zarr/example.zarr", mode="a")
        try:
            codex_store = pd.HDFStore(PATH_TO_CODEX_PVALS, mode="r")
        except:
            try:
                codex_store = pd.HDFStore(PATH_TO_CODEX_PVALS, mode="a")
            except:
                codex_store = pd.HDFStore("/opt/codex_fake.hdf5", mode="a")
