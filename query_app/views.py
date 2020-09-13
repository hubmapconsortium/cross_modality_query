from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.response import Response
from django.shortcuts import redirect

from .serializers import (
    CellSerializer,
    Cell_GroupingSerializer,
    GeneSerializer,
)

from .models import (
    Cell,
    Cell_Grouping,
    Gene,
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
)
from django.views.generic.edit import FormView


class CellViewSet(viewsets.ModelViewSet):
    queryset = Cell.objects.all()
    serializer_class = CellSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        input_type = self.request.query_params.get('input_type', None)
        input_set = self.request.query_params.get('input_set', None)
        logical_operator = self.request.query_params.get('logical_operator', None)
        response = cell_query(self, request, input_type, input_set, logical_operator)
        return Response(response)


class Cell_GroupingViewSet(viewsets.ModelViewSet):
    queryset = Cell_Grouping.objects.all()
    serializer_class = Cell_GroupingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        input_type = self.request.query_params.get('input_type', None)
        input_set = self.request.query_params.get('input_set', None)
        logical_operator = self.request.query_params.get('logical_operator', None)
        response = group_query(self, request, input_type, input_set, logical_operator)
        return Response(response)


class GeneViewSet(viewsets.ModelViewSet):
    queryset = Gene.objects.all()
    serializer_class = GeneSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        input_type = self.request.query_params.get('input_type', None)
        input_set = self.request.query_params.get('input_set', None)
        logical_operator = self.request.query_params.get('logical_operator', None)
        response = gene_query(self, request, input_type, input_set, logical_operator)
        return Response(response)


# class ProteinViewSet(viewsets.ModelViewSet):
#    queryset = Protein.objects.all()
#    serializer_class = ProteinSerializer
#    permission_classes = [permissions.IsAuthenticated]

class GeneQueryView(FormView):
    form_class = GeneQueryForm

    def form_valid(self, form):
        input_type = form.cleaned_data['input_type']
        input_set = form.cleaned_data['input_set']
        logical_operator = form.cleaned_data['logical_operator']
        response = gene_query(self, None, input_type, input_set, logical_operator)
        return Response(response)


class OrganQueryView(FormView):
    form_class = OrganQueryForm

    def form_valid(self, form):
        input_type = form.cleaned_data['input_type']
        input_set = form.cleaned_data['input_set']
        logical_operator = form.cleaned_data['logical_operator']
        response = group_query(self, None, input_type, input_set, logical_operator)
        return Response(response)


class CellQueryView(FormView):
    form_class = CellQueryForm

    def form_valid(self, form):
        input_type = form.cleaned_data['input_type']
        input_set = form.cleaned_data['input_set']
        logical_operator = form.cleaned_data['logical_operator']
        response = cell_query(self, None, input_type, input_set, logical_operator)
        return Response(response)


class LandingFormView(FormView):
    form_class = QueryForm

    def form_valid(self, form):
        if form.cleaned_data['output_type'] == 'Gene':
            return redirect(GeneQueryView)
        elif form.cleaned_data['output_type'] == 'Cell':
            return redirect(CellQueryView)
        elif form.cleaned_data['output_type'] == 'Organ':
            return redirect(OrganQueryView)
