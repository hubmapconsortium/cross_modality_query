from django.contrib import admin
from django.urls import path

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

]
