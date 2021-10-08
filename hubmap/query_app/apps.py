import anndata
import pandas as pd
from django.apps import AppConfig

PATH_TO_H5AD_FILES = "/opt/"

PATH_TO_CODEX_H5AD = PATH_TO_H5AD_FILES + "codex.h5ad"
PATH_TO_RNA_H5AD = PATH_TO_H5AD_FILES + "rna.h5ad"
PATH_TO_ATAC_H5AD = PATH_TO_H5AD_FILES + "atac.h5ad"
PATH_TO_RNA_PVALS = PATH_TO_H5AD_FILES + "rna.hdf5"
PATH_TO_ATAC_PVALS = PATH_TO_H5AD_FILES + "atac.hdf5"
PATH_TO_RNA_PERCENTAGES = PATH_TO_H5AD_FILES + "rna_precompute.hdf5"
PATH_TO_ATAC_PERCENTAGES = PATH_TO_H5AD_FILES + "atac_precompute.hdf5"
PATH_TO_CODEX_PERCENTAGES = PATH_TO_H5AD_FILES + "codex_precompute.hdf5"


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
        global rna_cell_df
        global atac_cell_df
        codex_adata = anndata.read(PATH_TO_CODEX_H5AD)
        rna_adata = anndata.read(PATH_TO_RNA_H5AD)
        atac_adata = anndata.read(PATH_TO_ATAC_H5AD)
        print("Quant adatas read in")
        #        rna_pvals = get_pval_df(PATH_TO_RNA_PVALS)
        #        atac_pvals = get_pval_df(PATH_TO_ATAC_PVALS)
        print("Pvals read in")
        rna_percentages = pd.read_hdf(PATH_TO_RNA_PERCENTAGES, "percentages")
        atac_percentages = pd.read_hdf(PATH_TO_ATAC_PERCENTAGES, "percentages")
        codex_percentages = pd.read_hdf(PATH_TO_CODEX_PERCENTAGES, "percentages")
        print("Everything read in")

        return
