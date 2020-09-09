#Write a view for each model in models.py
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.parsers import JSONParser
from rest_framework.response import Response


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

from .utils import(
    cell_query,
    gene_query,
    group_query,
)

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

#class ProteinViewSet(viewsets.ModelViewSet):
#    queryset = Protein.objects.all()
#    serializer_class = ProteinSerializer
#    permission_classes = [permissions.IsAuthenticated]

class GeneQueryView(viewsets.FormViewSet):
    form_class = GeneQueryForm

    def get(self, request, form):
        input_type = form.input_type
        input_set = form.input_set
        logical_operator = form.logical_operator
        response = gene_query(self, request, input_type, input_set, logical_operator)
        return Response(response)

class OrganQueryView(viewsets.FormViewSet):

    form_class = OrganQueryForm

    def get(self, request, form):
        input_type = form.input_type
        input_set = form.input_set
        logical_operator = form.logical_operator
        response = group_query(self, request, input_type, input_set, logical_operator)
        return Response(response)

class CellQueryView(viewsets.FormViewSet):

    form_class = CellQueryForm

    def get(self, request, form):
        input_type = form.input_type
        input_set = form.input_set
        logical_operator = form.logical_operator
        response = cell_query(self, request, input_type, input_set, logical_operator)
        return Response(response)



class LandingFormView(viewsets.FormViewSet):

    form_class = QueryForm

    def redirect_query(self, request, form):
        if form.output_type == 'Gene':
            return redirect(GeneQueryView)
        elif form.output_type == 'Cell':
            return redirect(CellQueryView)
        elif form.output_type == 'Organ':
            return redirect(OrganQueryView)