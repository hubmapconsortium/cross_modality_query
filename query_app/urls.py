from django.contrib import admin
from django.urls import path
from rest_framework.schemas import get_schema_view

from query_app import views

admin.autodiscover()
# first we define the serializers

urlpatterns = [
    path('query/', views.LandingFormView.as_view(), name="landing_page"),
    path('query/gene/', views.GeneViewSet.as_view({'post': 'post', 'get': 'get'}), name="gene_query"),
    path('query/cell/', views.CellViewSet.as_view({'post': 'post', 'get': 'get'}), name="cell_query"),
    path('query/organ/', views.CellGroupingViewSet.as_view({'post': 'post', 'get': 'get'}), name="organ_query"),
    path('query/protein/', views.ProteinViewSet.as_view({'get': 'get'}), name="protein_query"),
    path('query/geneform/', views.GeneQueryView.as_view(), name="gene_query_form"),
    path('query/cellform/', views.CellQueryView.as_view(), name="cell_query_form"),
    path('query/organform/', views.OrganQueryView.as_view(), name="organ_query_form"),
    path('query/celllist/', views.CellListView.as_view(), name="cell_list"),
    path('query/genelist/', views.GeneListView.as_view(), name="gene_list"),
    path('query/organlist/', views.OrganListView.as_view(), name="organ_list"),
    path('query/allcelllist/', views.AllCellListView.as_view(), name="all_cell_list"),
    path('query/allgenelist/', views.AllGeneListView.as_view(), name="all_gene_list"),
    path('query/allorganlist/', views.AllOrganListView.as_view(), name="all_organ_list"),
    path('query/allproteinlist/', views.AllProteinListView.as_view(), name="all_protein_list"),
    path(
        'openapi',
        get_schema_view(
            title="HuBMAP cell indexing",
            version="0.1-dev",
        ),
        name='openapi-schema',
    ),
]
