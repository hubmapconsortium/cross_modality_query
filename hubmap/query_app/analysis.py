from statistics import mean, stdev

import numpy as np

from .apps import atac_adata, codex_adata, rna_adata
from .utils import unpickle_query_set
from .validation import validate_bounds_args, validate_statistic_args

adatas = [codex_adata, rna_adata, atac_adata]


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


def get_adata_subset(adata, var_id, cell_ids):
    adata = adata[cell_ids, :]
    if len(adata.obs.index) == 0 or var_id not in adata.var.index:
        return None
    else:
        return adata[:, [var_id]]


def get_statistic_value(adata, stat_type):
    if not adata:
        return None
    else:
        if stat_type == "mean":
            value = adata.X.mean()
            if not value >= 0 and not isinstance(adata.X, np.ndarray):
                data_list = adata.X.todense().flatten().tolist()
                if isinstance(data_list[0], list):
                    data_list = data_list[0]
                data_list = check_list(data_list)
                #                value = adata.X.todense().mean()
                value = mean(data_list)
        elif stat_type == "min":
            value = adata.X.min()
            if not value >= 0 and not isinstance(adata.X, np.ndarray):
                data_list = adata.X.data.tolist()
                value = min(data_list)
        elif stat_type == "max":
            value = adata.X.max()
            if not value >= 0 and not isinstance(adata.X, np.ndarray):
                data_list = adata.X.data.tolist()
                value = max(data_list)
        elif stat_type == "stddev":
            if not isinstance(adata.X, np.ndarray):
                value = adata.X.todense().std()
            else:
                value = adata.X.std()
            if not value >= 0 and not isinstance(adata.X, np.ndarray):
                data_list = adata.X.todense().flatten().tolist()
                if isinstance(data_list[0], list):
                    data_list = data_list[0]
                data_list = check_list(data_list)
                value = stdev(data_list)

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

    codex_adata = get_adata_subset(adatas[0], var_id, codex_cells)
    rna_adata = get_adata_subset(adatas[1], var_id, rna_cells)
    atac_adata = get_adata_subset(adatas[2], var_id, atac_cells)

    print("Quants for each modality found")

    codex_value = get_statistic_value(codex_adata, stat_type)
    rna_value = get_statistic_value(rna_adata, stat_type)
    atac_value = get_statistic_value(atac_adata, stat_type)

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

    modalities_dict = {"rna": rna_adata, "atac": atac_adata, "codex": codex_adata}
    adata = modalities_dict[modality]

    if "var_id" in query_params.keys():
        min_value = float(adata.var.at[query_params["var_id"], "min"])
        max_value = float(adata.var.at[query_params["var_id"], "max"])
    else:
        min_value = float(adata.uns["min"])
        max_value = float(adata.uns["max"])

    return {"results": {"minimum_value": min_value, "maximum_value": max_value}}
