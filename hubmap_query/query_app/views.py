#Write a view for each model in models.py
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.parsers import JSONParser
from rest_framework.response import Response


from .serializers import (
    CellSerializer,
    Cell_GroupingSerializer,
    GeneSerializer,
    ProteinSerializer,
    ATAC_QuantSerializer,
    RNA_QuantSerializer,
)

from .models import (
    Cell,
    Cell_Grouping,
    Gene,
)

class CellViewSet(viewsets.ModelViewSet):
    queryset = Cell.objects.all()
    serializer_class = CellSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, response, format=None):
        response = cell_query(self, response)
        return Response(response)

class Cell_GroupingViewSet(viewsets.ModelViewSet):
    queryset = Cell_Grouping.objects.all()
    serializer_class = Cell_GroupingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, response, format=None):
        response = group_query(self, response)
        return Response(response)

class GeneViewSet(viewsets.ModelViewSet):
    queryset = Gene.objects.all()
    serializer_class = GeneSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, response, format=None):
        response = gene_query(self, response)
        return Response(response)

#class ProteinViewSet(viewsets.ModelViewSet):
#    queryset = Protein.objects.all()
#    serializer_class = ProteinSerializer
#    permission_classes = [permissions.IsAuthenticated]
