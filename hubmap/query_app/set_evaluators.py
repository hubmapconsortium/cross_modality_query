from typing import List

from django.db.models import Case, IntegerField, Q, Sum, When

from .filters import get_cells_list, split_at_comparator
from .models import (
    AtacQuant,
    Cell,
    CellAndValues,
    Cluster,
    ClusterAndValues,
    CodexQuant,
    Dataset,
    DatasetAndValues,
    Gene,
    GeneAndValues,
    Organ,
    OrganAndValues,
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
)
from .utils import (
    get_response_from_query_handle,
    get_response_with_count_from_query_handle,
    unpickle_query_set,
)
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


def get_ordered_query_set(query_set, set_type, sort_by, values_type, limit, offset):
    sort_by_values = get_values(query_set, set_type, [sort_by], values_type)
    sort_by_dict = {}
    for key in sort_by_values:
        if sort_by in sort_by_values[key].keys():
            sort_by_dict[key] = sort_by_values[key][sort_by]
        else:
            sort_by_dict[key] = 0.0

    query_set = order_query_set(query_set, limit, sort_by_dict, offset)

    return query_set


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


def get_values(query_set, set_type, values, values_type, statistic="mean"):

    values_dict = {}

    if set_type == "cell":
        # values must be genes
        if values_type == "gene":
            pks = query_set.values_list("pk", flat=True)
            print(len(pks))
            query_set = Cell.objects.filter(pk__in=pks)
            print(query_set.count())
            query_set = (
                Cell.objects.filter(pk__in=pks)
                .prefetch_related("atac_quants")
                .prefetch_related("rna_quants")
            )
            atac_cells = query_set.filter(modality__modality_name="atac").values_list(
                "cell_id", flat=True
            )
            rna_cells = query_set.filter(modality__modality_name="rna").values_list(
                "cell_id", flat=True
            )

            print("Modality cells gotten")

            values_dict = {
                cell: {gene: get_quant_value(cell, gene, "rna") for gene in values}
                for cell in rna_cells
            }
            values_dict.update(
                {
                    cell: {gene: get_quant_value(cell, gene, "atac") for gene in values}
                    for cell in atac_cells
                }
            )

        elif values_type == "protein":
            pks = query_set.values_list("pk", flat=True)
            query_set = Cell.objects.filter(pk__in=pks)

            codex_cells = query_set.filter(modality__modality_name="codex").values_list(
                "cell_id", flat=True
            )

            values_dict = {
                cell: {protein: get_quant_value(cell, protein, "codex") for protein in values}
                for cell in codex_cells
            }

        return values_dict

    elif set_type == "gene":
        # values must be organs or clusters
        gene_ids = query_set.values_list("gene_symbol", flat=True)

        if values_type == "organ":
            organs = Organ.objects.filter(grouping_name__in=values).values_list("pk", flat=True)
            pvals = PVal.objects.filter(p_organ__in=organs).filter(
                p_gene__gene_symbol__in=gene_ids
            )
            for gene in query_set:
                gene_pvals = pvals.filter(p_gene__gene_symbol=gene.gene_symbol).values_list(
                    "p_organ__grouping_name", "value"
                )
                values_dict[gene.gene_symbol] = {gp[0]: gp[1] for gp in gene_pvals}

        elif values_type == "cluster":
            clusters = Cluster.objects.filter(grouping_name__in=values).values_list(
                "pk", flat=True
            )
            pvals = PVal.objects.filter(p_cluster__in=clusters).filter(
                p_gene__gene_symbol__in=gene_ids
            )
            for gene in query_set:
                gene_pvals = pvals.filter(p_gene__gene_symbol=gene.gene_symbol).values_list(
                    "p_cluster__grouping_name", "value"
                )
                values_dict[gene.gene_symbol] = {gp[0]: gp[1] for gp in gene_pvals}

        return values_dict

    elif set_type == "organ":
        # values must be genes
        pvals = PVal.objects.filter(p_organ__in=query_set.values_list("pk", flat=True)).filter(
            p_gene__gene_symbol__in=values
        )
        for organ in query_set:
            organ_pvals = pvals.filter(p_organ=organ).values_list("p_gene__gene_symbol", "value")
            values_dict[organ.grouping_name] = {op[0]: op[1] for op in organ_pvals}
        return values_dict

    elif set_type == "cluster":
        # values must be genes
        pvals = PVal.objects.filter(p_cluster__in=query_set.values_list("pk", flat=True)).filter(
            p_gene__gene_symbol__in=values
        )
        for cluster in query_set:
            cluster_pvals = pvals.filter(p_cluster=cluster).values_list(
                "p_gene__gene_symbol", "value"
            )
            values_dict[cluster.grouping_name] = {cp[0]: cp[1] for cp in cluster_pvals}
        return values_dict


def get_percentages(query_set, include_values, values_type):
    query_params = {
        "input_type": values_type,
        "input_set": include_values,
        "logical_operator": "and",
    }
    if values_type == "gene" and query_set.first():
        query_params["genomic_modality"] = query_set.first().modality.modality_name
    var_cell_pks = get_cells_list(query_params, input_set=include_values).values_list(
        "pk", flat=True
    )
    var_cells = (
        Cell.objects.filter(pk__in=var_cell_pks).only("pk", "dataset").select_related("dataset")
    )
    dataset_pks = var_cells.distinct("dataset").values_list("dataset", flat=True)

    aggregate_kwargs = {
        str(dataset_pk): Sum(Case(When(dataset=dataset_pk, then=1), output_field=IntegerField()))
        for dataset_pk in dataset_pks
    }
    dataset_counts = {
        dataset_pk: Cell.objects.filter(dataset=dataset_pk).count() for dataset_pk in dataset_pks
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


def make_cell_and_values(query_params):
    pickle_hash, include_values, sort_by, limit, offset = process_evaluation_args(query_params)

    query_set, set_type = unpickle_query_set(pickle_hash)

    if len(include_values) > 0:
        values_type = infer_values_type(include_values)
        validate_values_types(set_type, values_type)

    query_set = (
        query_set[offset:limit]
        if sort_by is None
        else get_ordered_query_set(query_set, "cell", sort_by, values_type, limit, offset)
    )

    print("Query_set sliced")

    values_dict = (
        {}
        if len(include_values) == 0
        else get_values(query_set, "cell", include_values, values_type)
    )

    cavs = []

    for cell in query_set:
        if values_type == "protein":
            values = {var: get_quant_value(cell.cell_id, var, "codex") for var in include_values}
        else:
            values = {} if cell.cell_id not in values_dict else values_dict[cell.cell_id]

        kwargs = {
            "cell_id": cell.cell_id,
            "dataset": cell.dataset,
            "modality": cell.modality,
            "organ": cell.organ,
            "values": values,
        }

        cav = CellAndValues(**kwargs)

        cav.save()

        cavs.append(cav)

    print("Cavs created")

    print(f"Num cav pks: {len(cavs)}")

    qs = CellAndValues.objects.filter(pk__in=cavs)

    print(f"Qs count: {qs.count()}")

    return qs


def make_gene_and_values(query_params):
    pickle_hash, include_values, sort_by, limit, offset = process_evaluation_args(query_params)

    query_set, set_type = unpickle_query_set(pickle_hash)

    if len(include_values) > 0:
        values_type = infer_values_type(include_values)
        validate_values_types(set_type, values_type)

    query_set = unpickle_query_set(pickle_hash)

    # Filter on timestamp

    query_set = (
        query_set[offset:limit]
        if sort_by is None
        else get_ordered_query_set(query_set, "gene", sort_by, values_type, limit, offset)
    )

    values_dict = (
        {}
        if len(include_values) == 0
        else get_values(query_set, "gene", include_values, values_type)
    )

    gavs = []

    for gene in query_set:
        values = {} if gene.gene_symbol not in values_dict else values_dict[gene.gene_symbol]
        kwargs = {"gene_symbol": gene.gene_symbol, "values": values}

        gav = GeneAndValues(**kwargs)
        gav.save()
        gavs.append(gav)

    # Filter on query hash
    return GeneAndValues.objects.filter(pk__in=gavs)


def make_organ_and_values(query_params):

    pickle_hash, include_values, sort_by, limit, offset = process_evaluation_args(query_params)
    query_set, set_type = unpickle_query_set(pickle_hash)

    if len(include_values) > 0:
        values_type = infer_values_type(include_values)
        validate_values_types(set_type, values_type)

    query_set = unpickle_query_set(pickle_hash)

    query_set = (
        query_set[offset:limit]
        if sort_by is None
        else get_ordered_query_set(query_set, "organ", sort_by, values_type, limit, offset)
    )

    values_dict = (
        {}
        if len(include_values) == 0
        else get_values(query_set, "organ", include_values, values_type)
    )

    oavs = []

    for organ in query_set:
        values = {} if organ.grouping_name not in values_dict else values_dict[organ.grouping_name]

        kwargs = {"grouping_name": organ.grouping_name, "values": values}
        oav = OrganAndValues(**kwargs)
        oav.save()
        oavs.append(oav)

    # Filter on query hash
    return OrganAndValues.objects.filter(pk__in=oavs)


def make_cluster_and_values(query_params):
    pickle_hash, include_values, sort_by, limit, offset = process_evaluation_args(query_params)
    query_set, set_type = unpickle_query_set(pickle_hash)

    if len(include_values) > 0:
        values_type = infer_values_type(include_values)
        validate_values_types(set_type, values_type)

    query_set = (
        query_set[offset:limit]
        if sort_by is None
        else get_ordered_query_set(query_set, "cluster", sort_by, values_type, limit, offset)
    )

    values_dict = (
        {}
        if len(include_values) == 0
        else get_values(query_set, "cluster", include_values, values_type)
    )

    clavs = []

    for cluster in query_set[:limit]:
        values = (
            {} if cluster.grouping_name not in values_dict else values_dict[cluster.grouping_name]
        )

        kwargs = {
            "grouping_name": cluster.grouping_name,
            "dataset": cluster.dataset,
            "values": values,
        }
        clav = ClusterAndValues(**kwargs)
        clav.save()
        clavs.append(clav)

    # Filter on query hash
    return ClusterAndValues.objects.filter(pk__in=clavs)


def make_dataset_and_values(query_params):
    pickle_hash, include_values, sort_by, limit, offset = process_evaluation_args(query_params)
    query_set, set_type = unpickle_query_set(pickle_hash)

    if len(include_values) > 0:
        values_type = infer_values_type(include_values)
        validate_values_types(set_type, values_type)

    query_set_pks = query_set[offset:limit].values_list("pk", flat=True)
    query_set = Dataset.objects.filter(pk__in=query_set_pks)

    print(len(include_values))

    values_dict = (
        {} if len(include_values) == 0 else get_percentages(query_set, include_values, values_type)
    )

    davs = []

    for dataset in query_set[:limit]:
        values = {} if dataset.pk not in values_dict else values_dict[dataset.pk]

        kwargs = {
            "uuid": dataset.uuid,
            "values": values,
        }
        dav = DatasetAndValues(**kwargs)
        dav.save()
        davs.append(dav)

    # Filter on query hash
    return DatasetAndValues.objects.filter(pk__in=davs)


def cell_evaluation_detail(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        if "values_included" in query_params.keys():
            query_params["values_included"] = request.POST.getlist("values_included")
        validate_detail_evaluation_args(query_params)
        evaluated_set = make_cell_and_values(query_params)
        self.queryset = evaluated_set
        # Set context
        context = {
            "request": request,
        }

        response = CellAndValuesSerializer(evaluated_set, many=True, context=context).data

        return response


def gene_evaluation_detail(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        if "values_included" in query_params.keys():
            query_params["values_included"] = request.POST.getlist("values_included")
        validate_detail_evaluation_args(query_params)
        evaluated_set = make_gene_and_values(query_params)
        self.queryset = evaluated_set
        # Set context
        context = {
            "request": request,
        }

        response = GeneAndValuesSerializer(evaluated_set, many=True, context=context).data

        return response


def organ_evaluation_detail(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        if "values_included" in query_params.keys():
            query_params["values_included"] = request.POST.getlist("values_included")
        validate_detail_evaluation_args(query_params)
        evaluated_set = make_organ_and_values(query_params)
        self.queryset = evaluated_set
        # Set context
        context = {
            "request": request,
        }

        response = OrganAndValuesSerializer(evaluated_set, many=True, context=context).data

        return response


def cluster_evaluation_detail(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        if "values_included" in query_params.keys():
            query_params["values_included"] = request.POST.getlist("values_included")
        validate_detail_evaluation_args(query_params)
        evaluated_set = make_cluster_and_values(query_params)
        self.queryset = evaluated_set
        # Set context
        context = {
            "request": request,
        }

        response = ClusterAndValuesSerializer(evaluated_set, many=True, context=context).data

        return response


def dataset_evaluation_detail(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        if "values_included" in query_params.keys():
            query_params["values_included"] = request.POST.getlist("values_included")
        validate_detail_evaluation_args(query_params)
        evaluated_set = make_dataset_and_values(query_params)
        self.queryset = evaluated_set
        # Set context
        context = {
            "request": request,
        }

        response = DatasetAndValuesSerializer(evaluated_set, many=True, context=context).data

        return response


def evaluate_qs(set_type, key, limit, offset):
    evaluated_set, set_type = unpickle_query_set(query_handle=key)
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
