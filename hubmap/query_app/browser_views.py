from django.shortcuts import redirect, render
from django.views.generic.edit import FormView
from django_tables2 import SingleTableView
from django_tables2.config import RequestConfig
from django_tables2.export.export import TableExport
from rest_framework.decorators import api_view

from .forms import (
    CellForm,
    ClusterQueryForm,
    CountForm,
    DatasetQueryForm,
    EvaluationForm,
    EvaluationLandingForm,
    GeneQueryForm,
    IntersectionForm,
    ListForm,
    NegationForm,
    OrganQueryForm,
    QueryForm,
    UnionForm,
)
from .models import (
    Cell,
    CellAndValues,
    Cluster,
    ClusterAndValues,
    Dataset,
    Gene,
    GeneAndValues,
    Organ,
    OrganAndValues,
    QuerySet,
)
from .queries import get_cells_list, get_clusters_list, get_genes_list, get_organs_list
from .set_evaluators import (
    evaluate_qs,
    get_qs_count,
    make_cell_and_values,
    make_cluster_and_values,
    make_gene_and_values,
    make_organ_and_values,
    query_set_count,
)
from .set_operators import (
    qs_intersect,
    qs_negate,
    qs_union,
    query_set_intersection,
    query_set_negation,
    query_set_union,
)
from .tables import (
    CellAndValuesTable,
    CellTable,
    ClusterAndValuesTable,
    ClusterTable,
    DatasetTable,
    GeneAndValuesTable,
    GeneTable,
    OrganAndValuesTable,
    OrganTable,
    QuerySetCountTable,
    QuerySetTable,
)
from .views import PaginationClass


class LandingFormView(FormView):
    form_class = QueryForm
    template_name = "landing_page.html"

    def post(self, request):
        if request.POST["output_type"] == "gene":
            return redirect("/api/geneform")
        elif request.POST["output_type"] == "cell":
            return redirect("/api/cellform")
        elif request.POST["output_type"] == "organ":
            return redirect("/api/organform")
        elif request.POST["output_type"] == "cluster":
            return redirect("/api/clusterform")
        elif request.POST["output_type"] == "dataset":
            return redirect("/api/datasetform")


class GeneQueryView(FormView):
    form_class = GeneQueryForm
    template_name = "query_form.html"

    def form_valid(self, form):
        return gene_detail(self.request)


class OrganQueryView(FormView):
    form_class = OrganQueryForm
    template_name = "query_form.html"

    def form_valid(self, form):
        return organ_detail(self.request)


class CellQueryView(FormView):
    form_class = CellForm
    template_name = "query_form.html"

    def form_valid(self, form):
        return cell_detail(self.request)


class ClusterQueryView(FormView):
    form_class = ClusterQueryForm
    template_name = "query_form.html"

    def form_valid(self, form):
        return cluster_list(self.request)


class DatasetQueryView(FormView):
    form_class = DatasetQueryForm
    template_name = "query_form.html"

    def form_valid(self, form):
        return dataset_list(self.request)


class SetIntersectionFormView(FormView):
    form_class = IntersectionForm
    template_name = "intersection_form.html"

    def form_valid(self, form):
        return query_set_intersection(self, self.request)


class SetUnionFormView(FormView):
    form_class = UnionForm
    template_name = "union_form.html"

    def form_valid(self, form):
        return query_set_union(self.request)


class SetNegationFormView(FormView):
    form_class = NegationForm
    template_name = "negation_form.html"

    def form_valid(self, form):
        return query_set_negation(self.request)


class SetCountFormView(FormView):
    form_class = CountForm
    template_name = "count_form.html"

    def form_valid(self, form):
        return query_set_count(self.request)


class EvaluationLandingFormView(FormView):
    form_class = EvaluationLandingForm
    template_name = "evaluation_form.html"

    def post(self, request):
        if request.POST["set_type"] == "gene":
            return redirect("/api/geneevaluationform")
        elif request.POST["set_type"] == "cell":
            return redirect("/api/cellevaluationform")
        elif request.POST["set_type"] == "organ":
            return redirect("/api/organevaluationform")
        elif request.POST["set_type"] == "cluster":
            return redirect("/api/clusterevaluationform")
        elif request.POST["set_type"] == "dataset":
            return redirect("/api/datasetevaluationform")


class CellSetEvaluationFormView(FormView):
    form_class = EvaluationForm
    template_name = "cell_evaluation_detail_form.html"

    def form_valid(self, form):
        return cell_detail(self.request)


class GeneSetEvaluationFormView(FormView):
    form_class = EvaluationForm
    template_name = "gene_evaluation_detail_form.html"

    def form_valid(self, form):
        return gene_detail(self.request)


class OrganSetEvaluationFormView(FormView):
    form_class = EvaluationForm
    template_name = "organ_evaluation_detail_form.html"

    def form_valid(self, form):
        return organ_detail(self.request)


class ClusterSetEvaluationFormView(FormView):
    form_class = EvaluationForm
    template_name = "cluster_evaluation_detail_form.html"

    def form_valid(self, form):
        return cluster_detail(self.request)


class CellSetListFormView(FormView):
    form_class = ListForm
    template_name = "cell_evaluation_list_form.html"

    def form_valid(self, form):
        return cell_list(self.request)


class GeneSetListFormView(FormView):
    form_class = ListForm
    template_name = "gene_evaluation_list_form.html"

    def form_valid(self, form):
        return gene_list(self.request)


class OrganSetListFormView(FormView):
    form_class = ListForm
    template_name = "organ_evaluation_list_form.html"

    def form_valid(self, form):
        return organ_list(self.request)


class ClusterSetListFormView(FormView):
    form_class = ListForm
    template_name = "cluster_evaluation_list_form.html"

    def form_valid(self, form):
        return cluster_list(self.request)


class DatasetSetListFormView(FormView):
    form_class = ListForm
    template_name = "dataset_evaluation_list_form.html"

    def form_valid(self, form):
        return dataset_list(self.request)


class CellDetailView(SingleTableView):
    model = CellAndValues
    table_class = CellAndValuesTable
    template_name = "cell_list.html"
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return cell_detail(request)


class GeneDetailView(SingleTableView):
    model = GeneAndValues
    table_class = GeneAndValuesTable
    template_name = "gene_list.html"
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return gene_detail(request)


class OrganDetailView(SingleTableView):
    model = OrganAndValues
    table_class = OrganAndValuesTable
    template_name = "organ_list.html"
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return organ_detail(request)


class ClusterDetailView(SingleTableView):
    model = ClusterAndValues
    table_class = ClusterAndValuesTable
    template_name = "cluster_list.html"
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return cluster_detail(request)


class CellListView(SingleTableView):
    model = Cell
    table_class = CellTable
    template_name = "cell_list.html"
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return cell_list(request)


class GeneListView(SingleTableView):
    model = Gene
    table_class = GeneTable
    template_name = "gene_list.html"
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return gene_list(request)


class OrganListView(SingleTableView):
    model = Organ
    table_class = OrganTable
    template_name = "organ_list.html"
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return organ_list(request)


class ClusterListView(SingleTableView):
    model = Cluster
    table_class = ClusterTable
    template_name = "cluster_list.html"
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return cluster_list(request)


class DatasetListView(SingleTableView):
    model = Dataset
    table_class = DatasetTable
    template_name = "dataset_list.html"
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return dataset_list(request)


class QuerySetListView(SingleTableView):
    model = QuerySet
    table_class = QuerySetTable
    template_name = "query_set_list.html"
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return query_set_list(request)


class QuerySetIntersectionListView(SingleTableView):
    model = QuerySet
    table_class = QuerySetTable
    template_name = "query_set_list.html"
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return query_set_intersection_list(request)


class QuerySetUnionListView(SingleTableView):
    model = QuerySet
    table_class = QuerySetTable
    template_name = "query_set_list.html"
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return query_set_union_list(request)


class QuerySetNegationListView(SingleTableView):
    model = QuerySet
    table_class = QuerySetTable
    template_name = "query_set_list.html"
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return query_set_negation_list(request)


class QuerySetCountListView(SingleTableView):
    model = QuerySet
    table_class = QuerySetCountTable
    template_name = "query_set_list.html"
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return query_set_count_list(request)


@api_view(["POST"])
def cell_detail(request):
    table = CellAndValuesTable(make_cell_and_values(request.data.dict()))
    print("Calling the right table")

    RequestConfig(request).configure(table)

    export_format = request.data.dict()["export_format"]
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "cell_list.html", {"table": table})


@api_view(["POST"])
def gene_detail(request):
    table = GeneAndValuesTable(make_gene_and_values(request.data.dict()))

    RequestConfig(request).configure(table)

    export_format = request.data.dict()["export_format"]

    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "gene_list.html", {"table": table})


@api_view(["POST"])
def organ_detail(request):
    table = OrganAndValuesTable(make_organ_and_values(request.data.dict()))

    RequestConfig(request).configure(table)

    export_format = request.data.dict()["export_format"]

    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "organ_list.html", {"table": table})


@api_view(["POST"])
def cluster_detail(request):
    table = ClusterAndValuesTable(make_cluster_and_values(request.data.dict()))

    RequestConfig(request).configure(table)

    export_format = request.data.dict()["export_format"]

    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "cluster_list.html", {"table": table})


@api_view(["POST"])
def cell_list(request):
    table = CellTable(evaluate_qs(request.data.dict()))
    print("Calling the right table")

    RequestConfig(request).configure(table)

    export_format = request.data.dict()["export_format"]
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "cell_list.html", {"table": table})


@api_view(["POST"])
def gene_list(request):
    table = GeneTable(evaluate_qs(request.data.dict()))

    RequestConfig(request).configure(table)

    export_format = request.data.dict()["export_format"]

    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "gene_list.html", {"table": table})


@api_view(["POST"])
def organ_list(request):
    table = OrganTable(evaluate_qs(request.data.dict()))

    RequestConfig(request).configure(table)

    export_format = request.data.dict()["export_format"]

    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "organ_list.html", {"table": table})


@api_view(["POST"])
def cluster_list(request):
    table = ClusterTable(evaluate_qs(request.data.dict()))

    RequestConfig(request).configure(table)

    export_format = request.data.dict()["export_format"]

    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "cluster_list.html", {"table": table})


@api_view(["POST"])
def dataset_list(request):
    table = DatasetTable(evaluate_qs(request.data.dict()))

    RequestConfig(request).configure(table)

    export_format = request.data.dict()["export_format"]

    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "dataset_list.html", {"table": table})


@api_view(["POST"])
def query_set_list(request, request_type="query"):
    if request_type == "intersection":
        table = QuerySetTable(query_set_intersection(request.data.dict()))
    elif request_type == "union":
        table = QuerySetTable(query_set_union(request.data.dict()))
    elif request_type == "negation":
        table = QuerySetTable(query_set_negation(request.data.dict()))
    elif request_type == "query":
        output_type = request.data.dict()["set_type"]
        if output_type == "gene":
            table = QuerySetTable(get_genes_list(request.data.dict()))
        elif output_type == "cell":
            table = QuerySetTable(get_cells_list(request.data.dict()))
        elif output_type == "organ":
            table = QuerySetTable(get_organs_list(request.data.dict()))
        elif output_type == "cluster":
            table = QuerySetTable(get_clusters_list(request.data.dict()))

    RequestConfig(request).configure(table)

    export_format = request.data.dict()["export_format"]

    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "query_set_list.html", {"table": table})


@api_view(["POST"])
def query_set_negation_list(request, request_type="query"):
    table = QuerySetTable(qs_negate(request.data.dict()))

    RequestConfig(request).configure(table)

    export_format = request.data.dict()["export_format"]

    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "query_set_list.html", {"table": table})


@api_view(["POST"])
def query_set_union_list(request, request_type="query"):
    table = QuerySetTable(qs_union(request.data.dict()))

    RequestConfig(request).configure(table)

    export_format = request.data.dict()["export_format"]

    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "query_set_list.html", {"table": table})


@api_view(["POST"])
def query_set_intersection_list(request, request_type="query"):
    table = QuerySetTable(qs_intersect(request.data.dict()))

    RequestConfig(request).configure(table)

    export_format = request.data.dict()["export_format"]

    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "query_set_list.html", {"table": table})


@api_view(["POST"])
def query_set_count_list(request, request_type="query"):
    table = QuerySetCountTable(get_qs_count(request.data.dict()))

    RequestConfig(request).configure(table)

    export_format = request.data.dict()["export_format"]

    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "query_set_list.html", {"table": table})
