import hashlib
import json
import pickle
from typing import List

from django.db import connections
from django.db.utils import OperationalError

from .models import Cell, Cluster, Dataset, Gene, Organ, Protein, QuerySet

modality_ranges_dict = {"rna": [0, 5], "atac": [-4, 1], "codex": [-1, -6]}
min_percentages = [10 * i for i in range(0, 11)]


def set_intersection(query_set_1, query_set_2):
    return query_set_1 & query_set_2


def set_union(query_set_1, query_set_2):
    return query_set_1 | query_set_2


def make_pickle_and_hash(qs, set_type):
    qry = qs.query
    query_pickle = pickle.dumps(qry)
    query_handle = str(hashlib.sha256(query_pickle).hexdigest())
    if QuerySet.objects.filter(query_handle=query_handle).first() is None:
        query_set = QuerySet(
            query_pickle=query_pickle, query_handle=query_handle, set_type=set_type
        )
        query_set.save()
    return query_handle


def unpickle_query_set(query_handle, set_type):

    print(query_handle)

    query_object = QuerySet.objects.filter(query_handle=query_handle).first()
    if query_object is None:
        raise ValueError(f"Query handle {query_handle} is not valid")
    query_pickle = query_object.query_pickle

    #    query_pickle = QuerySet.objects.get(query_handle=query_handle).query_pickle

    if set_type == "cell":
        qs = Cell.objects.all()

    elif set_type == "gene":
        qs = Gene.objects.all()

    elif set_type == "cluster":
        qs = Cluster.objects.all()

    elif set_type == "organ":
        qs = Organ.objects.all()

    elif set_type == "dataset":
        qs = Dataset.objects.all()

    elif set_type == "protein":
        qs = Protein.objects.all()

    qs.query = pickle.loads(query_pickle)

    return qs


def get_database_status():
    db_conn = connections["default"]
    try:
        c = db_conn.cursor()
    except OperationalError:
        connected = False
    else:
        connected = True
    return connected


def get_app_status():
    json_file_path = "/opt/cross-modality-query/version.json"
    with open(json_file_path) as file:
        json_dict = json.load(file)
        json_dict["Postgres connection"] = get_database_status()
        return json.dumps(json_dict)


def infer_values_type(values: List) -> str:

    print(values)

    values = [
        split_at_comparator(item)[0].strip()
        if len(split_at_comparator(item)) > 0
        else item.strip()
        for item in values
    ]

    print(values)

    values_up = [value.upper() for value in values]
    values = values + values_up

    print(values)

    """Assumes a non-empty list of one one type of entity, and no identifier collisions across entity types"""
    if Gene.objects.filter(gene_symbol__in=values).count() > 0:
        return "gene"
    if Protein.objects.filter(protein_id__in=values).count() > 0:
        return "protein"
    if Cluster.objects.filter(grouping_name__in=values).count() > 0:
        return "cluster"
    if Organ.objects.filter(grouping_name__in=values).count() > 0:
        return "organ"
    values.sort()
    raise ValueError(
        f"Value type could not be inferred. None of {values} recognized as gene, protein, cluster, or organ"
    )


def split_at_comparator(item: str) -> List:
    """str->List
    Splits a string representation of a quantitative comparison into its parts
    i.e. 'eg_protein>=50' -> ['eg_protein', '>=', '50']
    If there is no comparator in the string, returns an empty list"""

    comparator_list = ["<=", ">=", ">", "<", "==", "!="]
    for comparator in comparator_list:
        if comparator in item:
            item_split = item.split(comparator)
            item_split.insert(1, comparator)
            return item_split
    return []


def precompute_percentages():

    kwargs_list = []

    for modality in modality_ranges_dict:
        datasets = Dataset.objects.filter(modality__modality_name__iexact=modality)
        exponents = list(
            range(modality_ranges_dict[modality][0], modality_ranges_dict[modality][1] + 1)
        )

        if modality in ["atac", "rna"]:
            var_ids = Gene.objects.all().values_list("gene_symbol", flat=True)
            input_type = "gene"
            genomic_modality = modality

        elif modality in ["codex"]:
            var_ids = Protein.objects.all().values_list("protein_id", flat=True)
            input_type = "protein"
            genomic_modality = None

        modality = Modality.objects.filter(modality_name=modality)

        for exponent in exponents:

            cutoff = 10 ** exponent

            for var_id in var_ids:
                input_set = [f"{var_id} > {cutoff}"]
                query_params = {
                    "input_type": input_type,
                    "input_set": input_set,
                    "genomic_modality": genomic_modality,
                }
                cell_set = get_cells_list(query_params, input_set)
                for dataset in datasets:
                    params_tuple = (dataset.uuid, cell_set, input_set[0])
                    percentage = get_percentage_and_cache(params_tuple)
                    kwargs = {
                        "modality": modality,
                        "dataset": dataset,
                        "var_id": var_id,
                        "cutoff": cutoff,
                        "percentage": percentage,
                    }
                    kwargs_list.append(kwargs)

    objs = [PrecomputedPercentage(**kwargs) for kwargs in kwargs_list]
    PrecomputedPercentage.objects.bulk_create(objs)
