from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.response import Response
from django.shortcuts import redirect

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
)
from django.views.generic.edit import FormView


class CellViewSet(viewsets.ModelViewSet):
    queryset = Cell.objects.all()
    serializer_class = CellSerializer
    #permission_classes = [permissions.IsAuthenticated]
    model = Query

    def post(self, request, format=None):
        print(self.request.query_params)
        query_dict = self.request.query_params
        query_params = {kv[0]: kv[1] for kv in query_dict.lists()}
        print(query_params)
        response = group_query(self, request, query_params)
        return Response(response)


class CellGroupingViewSet(viewsets.ModelViewSet):
    queryset = CellGrouping.objects.all()
    serializer_class = CellGroupingSerializer
    #permission_classes = [permissions.IsAuthenticated]
    model = Query

    def post(self, request, format=None):
        query_dict = self.request.query_params
        query_params = {kv[0]: kv[1] for kv in query_dict.lists()}
        response = group_query(self, request, query_params)
        return Response(response)


class GeneViewSet(viewsets.ModelViewSet):
    queryset = Gene.objects.all()
    serializer_class = GeneSerializer
    #permission_classes = [permissions.IsAuthenticated]
    model = Query

    def post(self, request, format=None):
        query_dict = self.request.query_params
        query_params = {kv[0]: kv[1] for kv in query_dict.lists()}
        response = group_query(self, request, query_params)
        return Response(response)


# class ProteinViewSet(viewsets.ModelViewSet):
#    queryset = Protein.objects.all()
#    serializer_class = ProteinSerializer
#    permission_classes = [permissions.IsAuthenticated]

class GeneQueryView(FormView):
    form_class = GeneQueryForm
    model = Query

    def form_valid(self, form):
        query_params = form.cleaned_data
        response = gene_query(self, None, query_params)
        return Response(response)


class OrganQueryView(FormView):
    form_class = OrganQueryForm
    model = Query

    def form_valid(self, form):
        query_params = form.cleaned_data
        response = group_query(self, None, query_params)
        return Response(response)


class CellQueryView(FormView):
    form_class = CellQueryForm
    model = Query

    def form_valid(self, form):
        query_params = form.cleaned_data
        response = cell_query(self, None, query_params)
        return Response(response)


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
