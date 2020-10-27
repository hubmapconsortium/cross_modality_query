from django.shortcuts import redirect, render
from django.views.generic.edit import FormView
from django_tables2 import SingleTableView
from django_tables2.config import RequestConfig
from django_tables2.export.export import TableExport
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .forms import (
    QueryForm,
    CellForm,
    GeneQueryForm,
    OrganQueryForm,
)
from .models import (
    Cell,
    Gene,
    Organ,
    Protein,
    Query,
)
from .serializers import (
    CellSerializer,
    GeneSerializer,
    OrganSerializer,
    ProteinSerializer,
)
from .tables import (
    CellTable,
    CellAndValuesTable,
    GeneTable,
    GeneAndValuesTable,
    OrganTable,
    OrganAndValuesTable,
    ProteinTable,
)
from .utils import (
    cell_query,
    gene_query,
    organ_query,
    protein_query,
    get_cells_list,
    get_genes_list,
    get_organs_list,
    get_proteins_list,
)


class PaginationClass(PageNumberPagination):
    page_size = 10
    max_page_size = 10


class CellViewSet(viewsets.ModelViewSet):
    queryset = Cell.objects.all()
    serializer_class = CellSerializer
    pagination_class = PaginationClass
    model = Cell

    def post(self, request, format=None):
        response = cell_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response

    def get(self, request, format=None):
        response = cell_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class OrganViewSet(viewsets.ModelViewSet):
    queryset = Organ.objects.all()
    serializer_class = OrganSerializer
    model = Organ

    def post(self, request, format=None):
        response = organ_query(self, request)
        return Response(response)

    def get(self, request, format=None):
        response = organ_query(self, request)
        return Response(response)


class GeneViewSet(viewsets.ModelViewSet):
    queryset = Gene.objects.all()
    serializer_class = GeneSerializer
    pagination_class = PaginationClass
    model = Gene

    def post(self, request, format=None):
        response = gene_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response

    def get(self, request, format=None):
        response = gene_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class ProteinViewSet(viewsets.ModelViewSet):
    queryset = Protein.objects.all()
    serializer_class = ProteinSerializer
    pagination_class = PaginationClass

    def get(self, request, format=None):
        response = protein_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class GeneQueryView(FormView):
    form_class = GeneQueryForm
    model = Query
    template_name = "gene_form.html"

    def form_valid(self, form):
        return gene_list(self.request)


class OrganQueryView(FormView):
    form_class = OrganQueryForm
    model = Query
    template_name = "organ_form.html"

    def form_valid(self, form):
        return organ_list(self.request)


class CellQueryView(FormView):
    form_class = CellForm
    model = Query
    template_name = "cell_form.html"

    def form_valid(self, form):
        return cell_list(self.request)


class LandingFormView(FormView):
    form_class = QueryForm
    model = Query
    template_name = 'landing_page.html'

    def post(self, request):
        if request.POST['output_type'] == 'gene':
            return redirect('/api/geneform')
        elif request.POST['output_type'] == 'cell':
            return redirect('/api/cellform')
        elif request.POST['output_type'] == 'organ':
            return redirect('/api/organform')


class CellListView(SingleTableView):
    model = Cell
    table_class = CellAndValuesTable
    template_name = 'cell_list.html'
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return cell_list(request)


class GeneListView(SingleTableView):
    model = Gene
    table_class = GeneAndValuesTable
    template_name = 'gene_list.html'
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return gene_list(request)


class OrganListView(SingleTableView):
    model = Organ
    table_class = OrganAndValuesTable
    template_name = 'organ_list.html'
    paginator_class = PaginationClass

    def post(self, request, format=None):
        return organ_list(request)


class AllCellListView(SingleTableView):
    model = Cell
    table_class = CellTable
    template_name = 'cell_list.html'

    def post(self, request, format=None):
        return all_cell_list(request)


class AllGeneListView(SingleTableView):
    model = Gene
    table_class = GeneTable
    template_name = 'gene_list.html'

    def post(self, request, format=None):
        return all_gene_list(request)


class AllOrganListView(SingleTableView):
    model = Organ
    table_class = OrganTable
    template_name = 'organ_list.html'

    def post(self, request, format=None):
        return all_organ_list(request)


class AllProteinListView(SingleTableView):
    model = Protein
    table_class = ProteinTable
    template_name = 'protein_list.html'

    def post(self, request, format=None):
        return all_protein_list(request)


@api_view(['POST'])
def cell_list(request):
    if request.data.dict()['input_type'] == 'gene':
        table = CellAndValuesTable(get_cells_list(request.data.dict()))
        print('Calling the right table')
    else:
        table = CellAndValuesTable(get_cells_list(request.data.dict()))
        print('Calling the wrong table')

    RequestConfig(request).configure(table)

    export_format = request.data.dict()['export_format']
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "cell_list.html", {
        "table": table
    })


@api_view(['POST'])
def gene_list(request):

    table = GeneAndValuesTable(get_genes_list(request.data.dict()))

    RequestConfig(request).configure(table)

    export_format = request.data.dict()['export_format']

    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "gene_list.html", {
        "table": table
    })


@api_view(['POST'])
def organ_list(request):

    table = OrganAndValuesTable(get_organs_list(request.data.dict()))

    RequestConfig(request).configure(table)

    export_format = request.data.dict()['export_format']

    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    return render(request, "organ_list.html", {
        "table": table
    })


@api_view(['POST'])
def all_cell_list(request):
    table = CellTable(get_cells_list({'input_type': None}))

    return render(request, "cell_list.html", {
        "table": table
    })


@api_view(['POST'])
def all_gene_list(request):
    table = GeneTable(get_genes_list({'input_type': None}))

    return render(request, "gene_list.html", {
        "table": table
    })


@api_view(['POST'])
def all_organ_list(request):
    table = OrganTable(get_organs_list({'input_type': None}))

    return render(request, "organ_list.html", {
        "table": table
    })


@api_view(['POST'])
def all_protein_list(request):
    table = ProteinTable(get_proteins_list({'input_type': None}))

    return render(request, "organ_list.html", {
        "table": table
    })
