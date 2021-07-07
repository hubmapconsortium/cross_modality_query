import numpy as np
from django.db.models import Avg, Max, Min, StdDev, Sum

from .models import AtacQuant, CodexQuant, RnaQuant, StatReport
from .serializers import StatReportSerializer
from .utils import unpickle_query_set
from .validation import validate_max_value_args, validate_statistic_args


def get_num_zeros(cell_set, quant_set):
    num_zeroes = cell_set.count() - quant_set.count()
    print("num_zeroes found")
    return num_zeroes


def query_set_to_numpy(cell_set, quant_set):
    quant_values = quant_set.values_list("value", flat=True)
    num_zeroes = get_num_zeros(cell_set, quant_set)
    zero_values = [0] * num_zeroes
    quant_values = quant_values + zero_values
    return np.ndarray(quant_values)


def get_stat_values(query_set, var_id, stat_type):
    codex_cells = query_set.filter(modality__modality_name="codex")
    rna_cells = query_set.filter(modality__modality_name="rna")
    atac_cells = query_set.filter(modality__modality_name="atac")

    print("Cells for each modality found")

    codex_quants = CodexQuant.objects.filter(q_var_id=var_id).filter(
        q_cell_id__in=codex_cells.values_list("cell_id", flat=True)
    )
    rna_quants = RnaQuant.objects.filter(q_var_id=var_id).filter(
        q_cell_id__in=rna_cells.values_list("cell_id", flat=True)
    )
    atac_quants = AtacQuant.objects.filter(q_var_id=var_id).filter(
        q_cell_id__in=atac_cells.values_list("cell_id", flat=True)
    )

    print("Quants for each modality found")

    if stat_type == "mean":
        if get_num_zeros(rna_cells, rna_quants) > 0:
            rna_value = rna_quants.aggregate(Sum("value"))["value__avg"]
            rna_value = rna_value / rna_cells.count()
        else:
            rna_value = rna_quants.aggregate(Avg("value"))["value__avg"]

        print("RNA value found")

        if get_num_zeros(atac_cells, atac_quants) > 0:
            atac_value = atac_quants.aggregate(Sum("value"))["value__avg"]
            atac_value = atac_value / atac_cells.count()
        else:
            atac_value = atac_quants.aggregate(Avg("value"))["value__avg"]

        print("Atac value found")

        codex_value = codex_quants.aggregate(Avg("value"))["value__avg"]

        print("Codex value found")

    elif stat_type == "min":
        codex_value = codex_quants.aggregate(Min("value"))
        if get_num_zeros(rna_cells, rna_quants) > 0:
            rna_value = 0
        else:
            rna_value = rna_quants.aggregate(Min("value"))
        if get_num_zeros(atac_cells, atac_quants) > 0:
            atac_value = 0
        else:
            atac_value = atac_quants.aggregate(Min("value"))

    elif stat_type == "max":
        codex_value = codex_quants.aggregate(Max("value"))
        rna_value = rna_quants.aggregate(Max("value"))
        atac_value = atac_quants.aggregate(Max("value"))

    elif stat_type == "stddev":
        codex_value = codex_quants.aggregate(StdDev("value"))
        if get_num_zeros(rna_cells, rna_quants) > 0:
            rna_value = query_set_to_numpy(rna_cells, rna_quants).std()
        else:
            rna_value = rna_quants.aggregate(StdDev("value"))
        if get_num_zeros(atac_cells, atac_quants) > 0:
            atac_value = query_set_to_numpy(atac_cells, atac_quants).std()
        else:
            atac_value = atac_quants.aggregate(StdDev("value"))

    codex_cells_excluded = get_num_zeros(codex_cells, codex_quants)

    if not codex_cells_excluded:
        codex_cells_excluded = 0

    return codex_value, rna_value, atac_value, codex_cells_excluded


def calc_stats(query_handle, set_type, var_id, stat_type):
    print(f"Calc stats called")
    query_set = unpickle_query_set(query_handle, set_type)
    codex_value, rna_value, atac_value, codex_cells_excluded = get_stat_values(
        query_set, var_id, stat_type
    )
    stat_report = StatReport(
        query_handle=query_handle,
        var_id=var_id,
        statistic_type=stat_type,
        rna_value=rna_value,
        atac_value=atac_value,
        codex_value=codex_value,
        num_cells_excluded=codex_cells_excluded,
    )
    stat_report.save()
    stat_reports = (
        StatReport.objects.filter(query_handle=query_handle)
        .filter(var_id=var_id)
        .filter(statistic_type=stat_type)
        .order_by("pk")
    )
    print(f"Stat reports count: {stat_reports.count()}")
    return stat_reports


def calculate_statistics(self, request):
    query_params = request.data.dict()
    stat_type = request.path.split("/")[-2]
    query_params["stat_type"] = stat_type

    print(request.path)
    print(request.path.split("/"))
    print(stat_type)

    query_handle, set_type, var_id, stat_type = validate_statistic_args(query_params)

    existing_stat_reports = (
        StatReport.objects.filter(query_handle=query_handle)
        .filter(var_id=var_id)
        .filter(statistic_type=stat_type)
        .order_by("pk")
    )

    if existing_stat_reports.first() is not None:
        print(f"Existing stat reports found")
        query_set = existing_stat_reports

    else:
        query_set = calc_stats(query_handle, set_type, var_id, stat_type)

    self.queryset = query_set
    # Set context
    context = {
        "request": request,
    }

    response = StatReportSerializer(query_set, many=True, context=context).data

    return response


def get_max_value(self, request):
    query_params = request.data.dict()
    validate_max_value_args(query_params)
    modality = query_params["modality"]
    if modality == "codex":
        query_set = CodexQuant.objects.all()
    elif modality == "rna":
        query_set = RnaQuant.objects.all()
    elif modality == "atac":
        query_set = AtacQuant.objects.all()
    if "var_id" in query_params.keys():
        query_set = query_set.filter(q_var_id__iexact=query_params["var_id"])

    value = query_set.aggregate(Max("value"))

    value = value["value__max"]
    return {"results": {"maximum_value": value}}
