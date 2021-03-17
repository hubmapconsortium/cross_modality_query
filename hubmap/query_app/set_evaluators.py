from typing import List

from django.db.models import Q

from .models import (
    AtacQuant,
    Cell,
    CellAndValues,
    Cluster,
    ClusterAndValues,
    CodexQuant,
    Gene,
    GeneAndValues,
    Organ,
    OrganAndValues,
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


def get_values(query_set, set_type, values, values_type, statistic="mean"):

    values_dict = {}

    if set_type == "cell":
        # values must be genes
        if values_type == "gene":
            pks = query_set.values_list("pk", flat=True)
            query_set = Cell.objects.filter(pk__in=pks)
            atac_cells = query_set.filter(modality__modality_name="atac").values_list(
                "cell_id", flat=True
            )
            rna_cells = query_set.filter(modality__modality_name="rna").values_list(
                "cell_id", flat=True
            )

            atac_quants = AtacQuant.objects.filter(q_cell_id__in=atac_cells).filter(
                q_var_id__in=values
            )
            rna_quants = RnaQuant.objects.filter(q_cell_id__in=rna_cells).filter(
                q_var_id__in=values
            )

            for cell in atac_cells:
                cell_values = atac_quants.filter(q_cell_id=cell).values_list("q_var_id", "value")
                values_dict[cell] = {cv[0]: cv[1] for cv in cell_values}
            for cell in rna_cells:
                cell_values = rna_quants.filter(q_cell_id=cell).values_list("q_var_id", "value")
                values_dict[cell] = {cv[0]: cv[1] for cv in cell_values}

        elif values_type == "protein":
            pks = query_set.values_list("pk", flat=True)
            query_set = Cell.objects.filter(pk__in=pks)

            codex_cells = query_set.filter(modality__modality_name="codex").values_list(
                "cell_id", flat=True
            )

            codex_quants = (
                CodexQuant.objects.filter(q_cell_id__in=codex_cells)
                .filter(q_var_id__in=values)
                .filter(statistic=statistic)
            )

            for cell in codex_cells:
                cell_values = codex_quants.filter(q_cell_id=cell).values_list("q_var_id", "value")
                values_dict[cell] = {cv[0]: cv[1] for cv in cell_values}

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


def get_qs_count(query_params):
    pickle_hash = query_params["key"]
    set_type = query_params["set_type"]

    qs = unpickle_query_set(pickle_hash, set_type)
    query_set = QuerySet.objects.filter(query_handle=pickle_hash).first()
    query_set.count = qs.count()
    query_set.save()

    qs_count = QuerySet.objects.filter(query_handle=pickle_hash)
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


def make_cell_and_values(query_params):
    pickle_hash, include_values, sort_by, limit, offset = process_evaluation_args(query_params)

    qs = QuerySet.objects.filter(query_handle__icontains=pickle_hash).first()
    set_type = qs.set_type

    if len(include_values) > 0:
        values_type = infer_values_type(include_values)
        validate_values_types(set_type, values_type)

    query_set = unpickle_query_set(pickle_hash, set_type)

    query_set = (
        query_set[offset:limit]
        if sort_by is None
        else get_ordered_query_set(query_set, "cell", sort_by, values_type, limit, offset)
    )

    values_dict = (
        {}
        if len(include_values) == 0
        else get_values(query_set, "cell", include_values, values_type)
    )

    cavs = []

    for cell in query_set:
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

        kwargs = {
            "cell_id": cell.cell_id,
            "dataset": cell.dataset,
            "modality": cell.modality,
            "organ": cell.organ,
            "values": values,
        }

        cav = CellAndValues(**kwargs)
        cav.save()

    qs = CellAndValues.objects.filter(pk__in=cavs)

    return qs


def make_gene_and_values(query_params):
    pickle_hash, include_values, sort_by, limit, offset = process_evaluation_args(query_params)

    qs = QuerySet.objects.filter(query_handle__icontains=pickle_hash).first()
    set_type = qs.set_type

    if len(include_values) > 0:
        values_type = infer_values_type(include_values)
        validate_values_types(set_type, values_type)

    query_set = unpickle_query_set(pickle_hash, set_type)

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

    qs = QuerySet.objects.filter(query_handle__icontains=pickle_hash).first()
    set_type = qs.set_type

    if len(include_values) > 0:
        values_type = infer_values_type(include_values)
        validate_values_types(set_type, values_type)

    query_set = unpickle_query_set(pickle_hash, set_type)

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

    qs = QuerySet.objects.filter(query_handle__icontains=pickle_hash).first()
    set_type = qs.set_type

    if len(include_values) > 0:
        values_type = infer_values_type(include_values)
        validate_values_types(set_type, values_type)

    query_set = unpickle_query_set(pickle_hash, set_type)

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


def evaluate_qs(set_type, key, limit, offset):
    evaluated_set = unpickle_query_set(query_handle=key, set_type=set_type)
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
