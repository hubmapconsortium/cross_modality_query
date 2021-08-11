from datetime import datetime

from celery import shared_task
from django.conf import settings

from .filters import get_cells_list, get_percentage_and_cache
from .models import AtacQuant, Modality, Protein, QuerySet, RnaQuant
from .utils import modality_ranges_dict


@shared_task
def delete_expired_querysets():
    querysets = QuerySet.objects.filter(
        created__lt=datetime.now() - settings.QUERY_TOKEN_EXPIRATION
    )
    querysets.delete()


@shared_task
def precompute_dataset_percentages(dataset):
    modality = dataset.modality.modality_name
    kwargs_list = []
    exponents = list(
        range(modality_ranges_dict[modality][0], modality_ranges_dict[modality][1] + 1)
    )
    if modality in ["atac", "rna"]:
        var_ids = (
            AtacQuant.objects.all().distinct("q_var_id").values_list("q_var_id", flat=True)
            if modality == "atac"
            else RnaQuant.objects.all().distinct("q_var_id").values_list("q_var_id", flat=True)
        )
        input_type = "gene"
        genomic_modality = modality

    elif modality in ["codex"]:
        var_ids = Protein.objects.all().values_list("protein_id", flat=True)
        input_type = "protein"
        genomic_modality = None

    modality = Modality.objects.filter(modality_name=modality)

    for var_id in var_ids:
        zero = False
        for exponent in exponents:
            cutoff = 10 ** exponent
            input_set = [f"{var_id} > {cutoff}"]
            query_params = {
                "input_type": input_type,
                "input_set": input_set,
                "genomic_modality": genomic_modality,
            }
            cell_set = get_cells_list(query_params, input_set)

            print(dataset.uuid)
            params_tuple = (dataset.uuid, cell_set, input_set[0])
            percentage = 0.0 if zero else get_percentage_and_cache(params_tuple)
            if percentage == 0.0:
                print("Hit a zero")
                zero = True

            kwargs = {
                "modality": modality,
                "dataset": dataset,
                "var_id": var_id,
                "cutoff": cutoff,
                "percentage": percentage,
            }
            kwargs_list.append(kwargs)

    return kwargs_list
