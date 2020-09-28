from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import redirect, render
from django_tables2 import SingleTableView

from .serializers import (
    CellSerializer,
    CellGroupingSerializer,
    GeneSerializer,
)

from .models import (
    Cell,
    CellGrouping,
    Gene,
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
    get_cells_list,
    get_groupings_list,
    get_genes_list,
)

from .tables import (
    GeneTable,
    CellTable,
    OrganTable,
)

from django.views.generic.edit import FormView


class CellViewSet(viewsets.ModelViewSet):
    queryset = Cell.objects.all()
    serializer_class = CellSerializer
    model = Cell

    def post(self, request, format=None):
        response = cell_query(self, request)
        return Response(response)


class CellGroupingViewSet(viewsets.ModelViewSet):
    queryset = CellGrouping.objects.all()
    serializer_class = CellGroupingSerializer
    model = CellGrouping

    def post(self, request, format=None):
        response = group_query(self, request)
        return Response(response)


class GeneViewSet(viewsets.ModelViewSet):
    queryset = Gene.objects.all()
    serializer_class = GeneSerializer
    model = Gene

    def post(self, request, format=None):
        response = gene_query(self, request)
        return Response(response)


# class ProteinViewSet(viewsets.ModelViewSet):
#    queryset = Protein.objects.all()
#    serializer_class = ProteinSerializer

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
    template = 'landing_form.html'

    def form_valid(self, form):
        if form.cleaned_data['output_type'] == 'Gene':
            return redirect(GeneQueryView)
        elif form.cleaned_data['output_type'] == 'Cell':
            return redirect(CellQueryView)
        elif form.cleaned_data['output_type'] == 'Organ':
            return redirect(OrganQueryView)


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
