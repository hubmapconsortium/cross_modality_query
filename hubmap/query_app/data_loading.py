#!/usr/bin/env python

import re

from .filters import get_cells_list, get_percentage_and_cache
from .models import (
    AtacQuant,
    Cell,
    Cluster,
    CodexQuant,
    Dataset,
    Gene,
    Modality,
    Organ,
    PrecomputedPercentage,
    Protein,
    PVal,
    RnaQuant,
)
from .utils import modality_ranges_dict


def validate_ip_address(request):
    allowed_ip_regex = "128.182.96.*"
    ip = request.META["REMOTE_ADDR"]
    prog = re.compile(allowed_ip_regex)
    if not prog.match(ip):
        raise ValueError("IP not authorized for write operations")


def delete_old_data(request):
    validate_ip_address(request)
    modality = request.data.dict()["modality"]
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
        #        Protein.objects.all().delete()
        CodexQuant.objects.all().delete()


def set_up_cluster_relationships(request):
    validate_ip_address(request)
    cluster_cells_dict = request.data.dict()
    cluster_id = cluster_cells_dict["cluster"]
    cells_ids = cluster_cells_dict["cells"]
    cluster = Cluster.objects.filter(grouping_name=cluster_id).first()
    cells = Cell.objects.filter(cell_id__in=cells_ids).values_list("pk", flat=True)
    cluster.cells.add(*cells)


def get_foreign_keys(kwargs, model_name):
    if model_name == "cell":
        kwargs["modality"] = Modality.objects.filter(modality_name=kwargs["modality"]).first()
        kwargs["dataset"] = Dataset.objects.filter(uuid=kwargs["dataset"]).first()
        kwargs["organ"] = Organ.objects.filter(grouping_name=kwargs["organ"]).first()
    if model_name == "dataset":
        kwargs["modality"] = Modality.objects.filter(modality_name=kwargs["modality"]).first()
    if model_name == "cluster":
        kwargs["dataset"] = Dataset.objects.filter(uuid=kwargs["dataset"]).first()
    if model_name == "pvalue":
        kwargs["p_gene"] = Gene.objects.filter(gene_symbol=kwargs["p_gene"]).first()
        kwargs["modality"] = Modality.objects.filter(modality_name=kwargs["modality"]).first()
        p_organ_id = Organ.objects.filter(grouping_name=kwargs["grouping_name"]).first()
        if p_organ_id is not None:
            kwargs["p_organ"] = p_organ_id
        else:
            kwargs["p_cluster"] = Cluster.objects.filter(
                grouping_name=kwargs["grouping_name"]
            ).first()
    return kwargs


def create_model(request):
    validate_ip_address(request)
    request_dict = request.data.dict()
    model_name = request_dict["model_name"]
    kwargs_list = request_dict["kwargs_list"]

    if model_name == "cell":
        kwargs_list = [get_foreign_keys(kwargs, model_name) for kwargs in kwargs_list]
        objs = [Cell(**kwargs) for kwargs in kwargs_list]
        Cell.objects.bulk_create(objs)
    elif model_name == "gene":
        objs = [Gene(**kwargs) for kwargs in kwargs_list]
        Gene.objects.bulk_create(objs)
    elif model_name == "organ":
        objs = [Organ(**kwargs) for kwargs in kwargs_list]
        Organ.objects.bulk_create(objs)
    elif model_name == "protein":
        objs = [Protein(**kwargs) for kwargs in kwargs_list]
        Protein.objects.bulk_create(objs)
    elif model_name == "pvalue":
        kwargs_list = [get_foreign_keys(kwargs, model_name) for kwargs in kwargs_list]
        objs = [PVal(**kwargs) for kwargs in kwargs_list]
        PVal.objects.bulk_create(objs)
    elif model_name == "cluster":
        kwargs_list = [get_foreign_keys(kwargs, model_name) for kwargs in kwargs_list]
        objs = [Cluster(**kwargs) for kwargs in kwargs_list]
        Cluster.objects.bulk_create(objs)
    elif model_name == "dataset":
        kwargs_list = [get_foreign_keys(kwargs, model_name) for kwargs in kwargs_list]
        objs = [Dataset(**kwargs) for kwargs in kwargs_list]
        Dataset.objects.bulk_create(objs)
    elif model_name == "atacquant":
        objs = [AtacQuant(**kwargs) for kwargs in kwargs_list]
        AtacQuant.objects.bulk_create(objs)
    elif model_name == "codexquant":
        objs = [CodexQuant(**kwargs) for kwargs in kwargs_list]
        CodexQuant.objects.bulk_create(objs)
    elif model_name == "rnaquant":
        objs = [RnaQuant(**kwargs) for kwargs in kwargs_list]
        RnaQuant.objects.bulk_create(objs)
    elif model_name == "modality":
        objs = [Modality(**kwargs) for kwargs in kwargs_list]
        Modality.objects.bulk_create(objs)
    else:
        obj = None
    return obj


def precompute_percentages(request):
    validate_ip_address(request)
    modality = request.data.dict()["modality"]

    kwargs_list = []

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
