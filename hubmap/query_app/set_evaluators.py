import json
from typing import List

import pandas as pd
from django.db.models import Case, IntegerField, Q, Sum, When

from query_app.apps import (
    atac_adata,
    atac_cell_df,
    codex_adata,
    codex_cell_df,
    hash_dict,
    rna_adata,
    rna_cell_df,
)

from .filters import get_cells_list, split_at_comparator
from .models import (
    AtacQuant,
    Cell,
    Cluster,
    CodexQuant,
    Dataset,
    Gene,
    Organ,
    Protein,
    PVal,
    RnaQuant,
)
from .serializers import (
    CellAndValuesSerializer,
    CellSerializer,
    ClusterAndValuesSerializer,
    ClusterSerializer,
    DatasetAndValuesSerializer,
    DatasetSerializer,
    GeneAndValuesSerializer,
    GeneSerializer,
    OrganAndValuesSerializer,
    OrganSerializer,
    ProteinSerializer,
    get_quant_value,
)
from .utils import (
    get_response_from_query_handle,
    get_response_with_count_from_query_handle,
    infer_values_type,
    split_at_comparator,
    unpickle_query_set,
)
from .validation import (
    process_evaluation_args,
    validate_detail_evaluation_args,
    validate_list_evaluation_args,
    validate_values_types,
)


def annotate_with_values(cell_df, include_values, modality):
    if modality == "atac":
        adata = atac_adata
    elif modality == "codex":
        adata = codex_adata
    elif modality == "rna":
        adata = rna_adata

    cell_df = cell_df.set_index("cell_id", inplace=False, drop=False)

    cell_ids = list(cell_df["cell_id"])
    quant_df = adata.to_df()
    quant_df["cell_id"] = quant_df.index
    quant_df = quant_df[quant_df["cell_id"].isin(cell_ids)]
    quant_df = quant_df[include_values]

    values_dict = quant_df.to_dict(orient="index")
    values_list = [values_dict[i] for i in cell_df.index]
    values_series = pd.Series(values_list, index=cell_df.index)

    cell_df["values"] = values_series

    return cell_df


def annotate_list_with_values(dict_list, include_values, modality):
    for cell_dict in dict_list:
        cell_id = cell_dict["cell_id"]
        quant_values = {
            value: get_quant_value(cell_id, value, modality) for value in include_values
        }
        cell_dict["values"] = quant_values

    return dict_list


def get_dataset_cells(uuid, include_values, offset, limit):
    print("hash found")
    print(uuid)
    modality = (
        Dataset.objects.filter(uuid=uuid)
        .exclude(modality__isnull=True)
        .first()
        .modality.modality_name
    )
    if modality == "rna":
        cell_df = rna_cell_df
    elif modality == "atac":
        cell_df = atac_cell_df
    elif modality == "codex":
        cell_df = codex_cell_df

    cell_df = cell_df[cell_df["dataset"] == uuid]

    keep_columns = ["cell_id", "modality", "dataset", "organ", "clusters"]
    cell_df = cell_df[keep_columns]

    cell_df = cell_df[offset:limit]

    if len(include_values) > 0 and modality == "codex":
        cell_df = annotate_with_values(cell_df, include_values, modality)

    if type(list(cell_df["clusters"])[0]) == str:
        clusters_list = [clusters.split(",") for clusters in cell_df["clusters"]]
        cell_df["clusters"] = pd.Series(clusters_list, index=cell_df.index)

    cell_dict_list = cell_df.to_dict(orient="records")

    if len(include_values) > 0 and modality in ["atac", "rna"]:
        cell_dict_list = annotate_list_with_values(cell_dict_list, include_values, modality)

    return cell_dict_list


def get_max_value_items(query_set, limit, values_dict, offset):
    identifiers = []

    if query_set.count() == 0:
        return query_set.filter(pk__in=[])

    limit = min(limit, query_set.count())

    for i in range(limit):

        k = list(values_dict.keys())
        v = list(values_dict.values())

        if i >= offset:
            identifiers.append(k[v.index(max(v))])
        values_dict.pop(k[v.index(max(v))])

    if isinstance(query_set.first(), Cell):
        q = Q(cell_id__in=identifiers)

    elif isinstance(query_set.first(), Gene):
        q = Q(gene_symbol__in=identifiers)

    elif isinstance(query_set.first(), Organ):
        q = Q(grouping_name__in=identifiers)

    elif isinstance(query_set.first(), Cluster):
        q = Q(grouping_name__in=identifiers)

    return query_set.filter(q)


def order_query_set(query_set, limit, values_dict, offset):
    vals_dict = {}
    for item in query_set:
        if isinstance(item, Cell):
            identifier = item.cell_id
        elif isinstance(item, Gene):
            identifier = item.gene_symbol
        elif isinstance(item, Organ):
            identifier = item.grouping_name
        elif isinstance(item, Cluster):
            identifier = item.grouping_name

        if identifier in values_dict.keys():
            vals_dict[identifier] = values_dict[identifier]
        else:
            vals_dict[identifier] = 0.0

    return get_max_value_items(query_set, limit, vals_dict, offset)


def get_percentages(query_set, include_values, values_type):
    query_params = {
        "input_type": values_type,
        "input_set": include_values,
        "logical_operator": "and",
    }
    query_set = Dataset.objects.filter(pk__in=query_set.values_list("pk", flat=True))
    if values_type == "gene" and query_set.first():
        query_params["genomic_modality"] = query_set.first().modality.modality_name
    var_cell_pks = get_cells_list(query_params, input_set=include_values).values_list(
        "pk", flat=True
    )
    var_cells = (
        Cell.objects.filter(pk__in=var_cell_pks).only("pk", "dataset").select_related("dataset")
    )

    dataset_pks = set(list(var_cells.values_list("dataset", flat=True)))

    aggregate_kwargs = {
        str(dataset_pk): Sum(Case(When(dataset=dataset_pk, then=1), output_field=IntegerField()))
        for dataset_pk in dataset_pks
    }

    dataset_counts = {
        dataset_pk: Cell.objects.filter(dataset=dataset_pk).distinct("cell_id").count()
        for dataset_pk in dataset_pks
    }
    counts = var_cells.aggregate(**aggregate_kwargs)
    percentages_dict = {pk: counts[str(pk)] / dataset_counts[pk] * 100 for pk in dataset_pks}
    return percentages_dict


def get_qs_count(query_params):
    pickle_hash = query_params["key"]
    return get_response_with_count_from_query_handle(pickle_hash)


def query_set_count(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        return get_qs_count(query_params)


def evaluate_qs(set_type, key, limit, offset):
    evaluated_set = unpickle_query_set(query_handle=key, set_type=set_type)
    if set_type == "cell":
        evaluated_set = Cell.objects.filter(pk__in=evaluated_set.values_list("pk", flat=True))
        evaluated_set = evaluated_set.distinct("cell_id")
    elif set_type == "dataset":
        evaluated_set = Dataset.objects.filter(pk__in=evaluated_set.values_list("pk", flat=True))
        evaluated_set = evaluated_set.distinct("uuid")
    evaluated_set = evaluated_set[offset:limit]
    return evaluated_set


def evaluation_list(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        set_type = query_params["set_type"]
        validate_list_evaluation_args(query_params)
        key, include_values, sort_by, limit, offset = process_evaluation_args(query_params)

        if key in hash_dict:
            cell_dict_list = get_dataset_cells(hash_dict[key], include_values, offset, limit)
            print(len(cell_dict_list))
            print(type(cell_dict_list))
            return cell_dict_list

        eval_qs = evaluate_qs(set_type, key, limit, offset)
        self.queryset = eval_qs
        # Set context
        context = {
            "request": request,
        }

        if set_type == "cell":
            response = CellSerializer(eval_qs, many=True, context=context).data
        if set_type == "gene":
            response = GeneSerializer(eval_qs, many=True, context=context).data
        if set_type == "cluster":
            response = ClusterSerializer(eval_qs, many=True, context=context).data
        if set_type == "organ":
            response = OrganSerializer(eval_qs, many=True, context=context).data
        if set_type == "dataset":
            response = DatasetSerializer(eval_qs, many=True, context=context).data
        if set_type == "protein":
            response = ProteinSerializer(eval_qs, many=True, context=context).data

        return response


def evaluation_detail(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        set_type = query_params["set_type"]
        query_params["values_included"] = request.POST.getlist("values_included")
        validate_detail_evaluation_args(query_params)
        key, include_values, sort_by, limit, offset = process_evaluation_args(query_params)

        if key in hash_dict:
            cell_dict_list = get_dataset_cells(hash_dict[key], include_values, offset, limit)
            print(len(cell_dict_list))
            print(type(cell_dict_list))
            return cell_dict_list
        eval_qs = evaluate_qs(set_type, key, limit, offset)

        self.queryset = eval_qs
        # Set context
        context = {
            "request": request,
        }

        if set_type == "cell":
            response = CellAndValuesSerializer(eval_qs, many=True, context=context).data
        if set_type == "gene":
            response = GeneAndValuesSerializer(eval_qs, many=True, context=context).data
        if set_type == "cluster":
            response = ClusterAndValuesSerializer(eval_qs, many=True, context=context).data
        if set_type == "organ":
            response = OrganAndValuesSerializer(eval_qs, many=True, context=context).data
        if set_type == "dataset":
            response = DatasetAndValuesSerializer(eval_qs, many=True, context=context).data
        if set_type == "protein":
            response = ProteinSerializer(eval_qs, many=True, context=context).data

        return response


def evaluate_qs(set_type, key, limit, offset):
    evaluated_set, set_type = unpickle_query_set(query_handle=key)
    evaluated_set = evaluated_set[offset:limit]
    return evaluated_set
