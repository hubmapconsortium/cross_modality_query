from typing import List

from django.db.models import Case, IntegerField, Q, Sum, When

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
    QuerySet,
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
    QuerySetCountSerializer,
)
from .utils import unpickle_query_set
from .validation import (
    process_evaluation_args,
    validate_detail_evaluation_args,
    validate_list_evaluation_args,
    validate_values_types,
)


def infer_values_type(values: List) -> str:

    print(values)

    values = [
        split_at_comparator(item)[0].strip()
        if len(split_at_comparator(item)) > 0
        else item.strip()
        for item in values
    ]

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


def get_quant_value(cell_id, gene_symbol, modality):
    print(f"{cell_id}, {gene_symbol}, {modality}")
    if modality == "rna":
        quant = RnaQuant.objects.filter(q_var_id=gene_symbol).filter(q_cell_id=cell_id).first()
    if modality == "atac":
        quant = AtacQuant.objects.filter(q_var_id=gene_symbol).filter(q_cell_id=cell_id).first()
    elif modality == "codex":
        quant = CodexQuant.objects.filter(q_var_id=gene_symbol).filter(q_cell_id=cell_id).first()
        print("Quant found")

    return 0.0 if quant is None else quant.value


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
    set_type = query_params["set_type"]

    qs = unpickle_query_set(pickle_hash, set_type)
    query_set = QuerySet.objects.filter(query_handle=pickle_hash).first()
    query_set.count = qs.count()
    query_set.save()

    qs_count = QuerySet.objects.filter(query_handle=pickle_hash).filter(count__gte=0)
    return qs_count


def query_set_count(self, request):
    if request.method == "POST":
        query_params = request.data.dict()

    qs_count = get_qs_count(query_params)

    self.queryset = qs_count
    # Set context
    context = {
        "request": request,
    }

    response = QuerySetCountSerializer(qs_count, many=True, context=context).data

    return response


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
        validate_detail_evaluation_args(query_params)
        key, include_values, sort_by, limit, offset = process_evaluation_args(query_params)
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
