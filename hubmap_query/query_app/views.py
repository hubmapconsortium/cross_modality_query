#Write a view for each model in models.py
from django.contrib.auth.models import User, Group
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



class CellViewSet(viewsets.ModelViewSet):
    queryset = Cell.objects.all()
    serializer_class = CellSerializer
    permission_classes = [permissions.IsAuthenticated]

class Cell_GroupingViewSet(viewsets.ModelViewSet):
    queryset = Cell_Grouping.objects.all()
    serializer_class = Cell_GroupingSerializer
    permission_classes = [permissions.IsAuthenticated]

class GeneViewSet(viewsets.ModelViewSet):
    queryset = Gene.objects.all()
    serializer_class = GeneSerializer
    permission_classes = [permissions.IsAuthenticated]

#class ProteinViewSet(viewsets.ModelViewSet):
#    queryset = Protein.objects.all()
#    serializer_class = ProteinSerializer
#    permission_classes = [permissions.IsAuthenticated]

class ATAC_QuantViewSet(viewsets.ModelViewSet):
    queryset = ATAC_Quant.objects.all()
    serializer_class = ATAC_QuantSerializer
    permission_classes = [permissions.IsAuthenticated]

class RNA_QuantViewSet(viewsets.ModelViewSet):
    queryset = RNA_Quant.objects.all()
    serializer_class = RNA_QuantSerializer
    permission_classes = [permissions.IsAuthenticated]

class CategoricalQuery(generics.ListAPIView):
#    serializer_class =
    parser_classes = [JSONParser]
    versioning_class = versioning.QueryParameterVersioning

    def post(self, request):
        response = categorical_query(self, request)
        return Response(response)

class QuantitativeQuery(generics.ListAPIView):
#    serializer_class =
    parser_classes = [JSONParser]
    versioning_class = versioning.QueryParameterVersioning

    def post(self, request):
        response = quantitative_query(self, request)
        return Response(response)
