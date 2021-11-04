from pathlib import Path

import anndata
import pandas as pd
from django.apps import AppConfig
from django.conf import settings
from pymongo import MongoClient


def set_up_mongo():
    client = MongoClient(settings.MONGO_HOST_AND_PORT)
    db = client[settings.MONGO_DB_NAME][settings.MONGO_COLLECTION_NAME]
    db.create_index("created_at", expireAfterSeconds=settings.TOKEN_EXPIRATION_TIME)
    #    db.log_events.createIndex({"created_at": 1}, {expireAfterSeconds: TOKEN_EXPIRATION_TIME})


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


def compute_dataset_hashes():
    from .models import Cell, Dataset
    from .utils import make_pickle_and_hash

    hash_dict = {}
    for uuid in Dataset.objects.all().values_list("uuid", flat=True):
        query_set = Cell.objects.filter(dataset__uuid=uuid)
        hash = make_pickle_and_hash(query_set, "cell")
        hash_dict[hash] = uuid

    return hash_dict


def get_pval_df(path_to_pvals):
    with pd.HDFStore(path_to_pvals) as store:
        grouping_keys = ["organ", "cluster"]
        grouping_dfs = [store.get(key) for key in grouping_keys]
        return pd.concat(grouping_dfs)


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

        set_up_mongo()

        codex_adata = anndata.read(PATH_TO_CODEX_H5AD)
        rna_adata = anndata.read(PATH_TO_RNA_H5AD)
        rna_adata.var_names_make_unique()

        hash_dict = compute_dataset_hashes()

        atac_adata = anndata.read(PATH_TO_ATAC_H5AD)
        atac_adata.var_names_make_unique()
        print("Quant adatas read in")
        if settings.SKIP_LOADING_PVALUES:
            atac_pvals = pd.DataFrame()
            rna_pvals = pd.DataFrame()
        else:
            rna_pvals = get_pval_df(PATH_TO_RNA_PVALS)
            atac_pvals = get_pval_df(PATH_TO_ATAC_PVALS)
        print("Pvals read in")
        rna_percentages = pd.read_hdf(PATH_TO_RNA_PERCENTAGES, "percentages")
        atac_percentages = pd.read_hdf(PATH_TO_ATAC_PERCENTAGES, "percentages")
        codex_percentages = pd.read_hdf(PATH_TO_CODEX_PERCENTAGES, "percentages")
        print("Percentages read in")
        rna_cell_df = pd.read_hdf(PATH_TO_RNA_PVALS, "cell")
        atac_cell_df = pd.read_hdf(PATH_TO_ATAC_PVALS, "cell")
        codex_cell_df = pd.read_hdf(PATH_TO_CODEX_PVALS, "cell")
        codex_cell_df = codex_cell_df[~codex_cell_df["clusters"].isna()]
        # rna_cell_df = pd.DataFrame()
        # atac_cell_df = pd.DataFrame()
        # codex_cell_df = pd.DataFrame()


#        hash_dict = {}
