#!/usr/bin/env python

from time import perf_counter

from query_app.models import (
    AtacQuant,
    Cell,
    Cluster,
    CodexQuant,
    Dataset,
    Gene,
    Modality,
    Organ,
    Protein,
    PVal,
    RnaQuant,
)


def delete_old_data(request):

    start_time = perf_counter()

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
        Protein.objects.all().delete()
        CodexQuant.objects.all().delete()

    stop_time = perf_counter()

    return {"message": f"Records deleted for modality {modality}", "time": stop_time - start_time}


def set_up_cluster_relationships(request):

    start_time = perf_counter()

    cluster_cells_dict = request.data.dict()
    cluster_id = cluster_cells_dict["cluster"]
    cells_ids = cluster_cells_dict["cells"]
    cluster = Cluster.objects.filter(grouping_name=cluster_id).first()
    cells = Cell.objects.filter(cell_id__in=cells_ids).values_list("pk", flat=True)
    cluster.cells.add(*cells)

    stop_time = perf_counter()
    return {"message": "Relationships set up", "time": stop_time - start_time}


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
        kwargs.pop("grouping_name")
    if "quant" in model_name:
        kwargs["q_cell"] = Cell.objects.filter(cell_id=kwargs["q_cell_id"])
        kwargs.pop("q_cell_id")
        q_protein = Protein.objects.filter(protein_id=kwargs["q_var_id"]).first()
        if q_protein is not None:
            kwargs["q_protein"] = q_protein
        else:
            kwargs["q_gene"] = Gene.objects.filter(gene_symbol=kwargs["q_var_id"]).first()
        kwargs.pop("q_var_id")
    return kwargs


def create_model(request):

    start_time = perf_counter()

    request_dict = request.data.dict()
    model_name = request_dict["model_name"]
    kwargs_list = request_dict["kwargs_list"]

    if model_name == "cell":
        kwargs_list = [get_foreign_keys(kwargs, model_name) for kwargs in kwargs_list]
        objs = [Cell(**kwargs) for kwargs in kwargs_list]
        Cell.objects.bulk_create(objs)
    elif model_name == "gene":
        existing_genes = Gene.objects.all().values_list("gene_symbol", flat=True)
        objs = [
            Gene(**kwargs) for kwargs in kwargs_list if kwargs["gene_symbol"] not in existing_genes
        ]
        Gene.objects.bulk_create(objs)
    elif model_name == "organ":
        existing_organs = Organ.objects.all().values_list("grouping_name", flat=True)
        objs = [
            Organ(**kwargs)
            for kwargs in kwargs_list
            if kwargs["grouping_name"] not in existing_organs
        ]
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
        kwargs_list = [get_foreign_keys(kwargs, model_name) for kwargs in kwargs_list]
        objs = [AtacQuant(**kwargs) for kwargs in kwargs_list]
        AtacQuant.objects.bulk_create(objs)
    elif model_name == "codexquant":
        kwargs_list = [get_foreign_keys(kwargs, model_name) for kwargs in kwargs_list]
        objs = [CodexQuant(**kwargs) for kwargs in kwargs_list]
        CodexQuant.objects.bulk_create(objs)
    elif model_name == "rnaquant":
        kwargs_list = [get_foreign_keys(kwargs, model_name) for kwargs in kwargs_list]
        objs = [RnaQuant(**kwargs) for kwargs in kwargs_list]
        RnaQuant.objects.bulk_create(objs)
    elif model_name == "modality":
        objs = [Modality(**kwargs) for kwargs in kwargs_list]
        Modality.objects.bulk_create(objs)
    else:
        objs = []

    stop_time = perf_counter()

    return {"message": f"{len(objs)} {model_name}s created", "time": stop_time - start_time}
