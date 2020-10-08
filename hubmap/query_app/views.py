from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import redirect, render
from django_tables2 import SingleTableView

from .serializers import (
    CellSerializer,
    CellGroupingSerializer,
    GeneSerializer,
    ProteinSerializer,
)

from .models import (
    Cell,
    CellGrouping,
    Gene,
    Protein,
    Query,
)

from .forms import (
    QueryForm,
    CellQueryForm,
    GeneQueryForm,
    OrganQueryForm,
)

from .utils import (
    cell_query,
    gene_query,
    group_query,
    protein_query,
    get_cells_list,
    get_groupings_list,
    get_genes_list,
    get_proteins_list,
)

from .tables import (
    GeneTable,
    CellTable,
    OrganTable,
    ProteinTable,
)

from django.views.generic.edit import FormView


class CellViewSet(viewsets.ModelViewSet):
    queryset = Cell.objects.all()
    serializer_class = CellSerializer
    model = Cell

    def post(self, request, format=None):
        response = cell_query(self, request)
        return Response(response)

    def get(self, request, format=None):
        response = cell_query(self, request)
        return Response(response)


class CellGroupingViewSet(viewsets.ModelViewSet):
    queryset = CellGrouping.objects.all()
    serializer_class = CellGroupingSerializer
    model = CellGrouping

    def post(self, request, format=None):
        response = group_query(self, request)
        return Response(response)

    def get(self, request, format=None):
        response = group_query(self, request)
        return Response(response)


class GeneViewSet(viewsets.ModelViewSet):
    queryset = Gene.objects.all()
    serializer_class = GeneSerializer
    model = Gene

    def post(self, request, format=None):
        response = gene_query(self, request)
        return Response(response)

    def get(self, request, format=None):
        response = gene_query(self, request)
        return Response(response)


class ProteinViewSet(viewsets.ModelViewSet):
    queryset = Protein.objects.all()
    serializer_class = ProteinSerializer

    def get(self, request, format=None):
        response = protein_query(self, request)
        return Response(response)


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
        return group_list(self.request)


class CellQueryView(FormView):
    form_class = CellQueryForm
    model = Query
    template_name = "cell_form.html"

    def form_valid(self, form):
        return group_list(self.request)


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
    table_class = CellTable
    template_name = 'cell_list.html'

    def post(self, request, format=None):
        return cell_list(request)


class GeneListView(SingleTableView):
    model = Gene
    table_class = GeneTable
    template_name = 'gene_list.html'

    def post(self, request, format=None):
        return gene_list(request)


class OrganListView(SingleTableView):
    model = CellGrouping
    table_class = OrganTable
    template_name = 'organ_list.html'

    def post(self, request, format=None):
        return group_list(request)

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
    model = CellGrouping
    table_class = OrganTable
    template_name = 'organ_list.html'

    def post(self, request, format=None):
        return all_group_list(request)

class AllProteinListView(SingleTableView):
    model = Protein
    table_class = ProteinTable
    template_name = 'protein_list.html'

    def post(self, request, format=None):
        return all_protein_list(request)

@api_view(['POST'])
def cell_list(request):
    table = CellTable(get_cells_list(request.data.dict()))

    return render(request, "cell_list.html", {
        "table": table
    })


@api_view(['POST'])
def gene_list(request):
    table = GeneTable(get_genes_list(request.data.dict()))

    return render(request, "gene_list.html", {
        "table": table
    })


@api_view(['POST'])
def group_list(request):
    table = OrganTable(get_groupings_list(request.data.dict()))

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
def all_group_list(request):
    table = OrganTable(get_groupings_list({'input_type': None}))

    return render(request, "organ_list.html", {
        "table": table
    })

@api_view(['POST'])
def all_protein_list(request):
    table = ProteinTable(get_proteins_list({'input_type': None}))

    return render(request, "organ_list.html", {
        "table": table
    })