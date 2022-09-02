from statistics import mean, stdev

import numpy as np
from typing import List

from .apps import (
    atac_cell_df,
    atac_gene_df,
    codex_cell_df,
    codex_gene_df,
    rna_cell_df,
    rna_gene_df,
    zarr_root,
)
from .utils import unpickle_query_set
from .validation import validate_bounds_args, validate_statistic_args

cell_dfs_dict = {"atac": atac_cell_df, "codex": codex_cell_df, "rna": rna_cell_df}


def check_list(vals_list):
    good_vals = []
    bad_vals = []
    for val in vals_list:
        little_list = [val]
        try:
            if mean(little_list) >= 0:
                good_vals.append(val)
            else:
                bad_vals.append(val)
        except:
            bad_vals.append(val)
    return good_vals


def get_data(modality:str, var_id:str, cell_ids:List[str]):
    bool_mask = cell_df.cell_id.isin(cell_ids)
    a = zarr_root[f"/{modality}/{var_id}/"][bool_mask]
    return a


def get_statistic_value(a, stat_type):
    if stat_type == "mean":
        value = a.mean()
    elif stat_type == "min":
        value = a.min()
    elif stat_type == "max":
        value = adata.X.max()
    elif stat_type == "stddev":
        value = adata.X.std()

    return float(value)


def get_stat_values(query_set, var_id, stat_type):

    codex_cells = list(
        query_set.filter(modality__modality_name="codex").values_list("cell_id", flat=True)
    )
    rna_cells = list(
        query_set.filter(modality__modality_name="rna").values_list("cell_id", flat=True)
    )
    atac_cells = list(
        query_set.filter(modality__modality_name="atac").values_list("cell_id", flat=True)
    )

    print("Cells for each modality found")

    codex_array = get_data("codex", var_id, codex_cells)
    rna_array = get_data("rna", var_id, rna_cells)
    atac_array = get_data("atac", var_id, atac_cells)

    codex_value = get_statistic_value(codex_array, stat_type)
    rna_value = get_statistic_value(rna_array, stat_type)
    atac_value = get_statistic_value(atac_array, stat_type)

    return codex_value, rna_value, atac_value


def calc_stats(query_handle, set_type, var_id, stat_type):
    print(f"Calc stats called")
    query_set = unpickle_query_set(query_handle)[0]
    codex_value, rna_value, atac_value = get_stat_values(query_set, var_id, stat_type)
    stat_report_dict = {
        "query_handle": query_handle,
        "var_id": var_id,
        "statistic_type": stat_type,
        "rna_value": rna_value,
        "atac_value": atac_value,
        "codex_value": codex_value,
    }

    response_dict = {}

    response_dict["count"] = 1
    response_dict["next"] = None
    response_dict["previous"] = None
    response_dict["results"] = [stat_report_dict]

    return response_dict


def calculate_statistics(self, request):
    query_params = request.data.dict()
    stat_type = request.path.split("/")[-2]
    query_params["stat_type"] = stat_type

    print(request.path)
    print(request.path.split("/"))
    print(stat_type)

    query_handle, set_type, var_id, stat_type = validate_statistic_args(query_params)

    stat_report_dict = calc_stats(query_handle, set_type, var_id, stat_type)

    return stat_report_dict


def get_bounds(self, request):
    query_params = request.data.dict()
    validate_bounds_args(query_params)
    modality = query_params["modality"]

    gene_dfs_dict = {"atac": atac_gene_df, "codex": codex_gene_df, "rna": rna_gene_df}
    gene_df = gene_dfs_dict[modality]

    if "var_id" in query_params.keys():
        min_value = gene_df.at[query_params["var_id"], "min"]
        max_value = gene_df.at[query_params["var_id"], "max"]
    else:
        min_value = gene_df["min"].min()
        max_value = gene_df["max"].max()

    return {"results": {"minimum_value": float(min_value), "maximum_value": float(max_value)}}
