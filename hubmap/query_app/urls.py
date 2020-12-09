from django.contrib import admin
from django.urls import path
from rest_framework.schemas import get_schema_view

from query_app import views

admin.autodiscover()
# first we define the serializers

urlpatterns = [
    path("", views.LandingFormView.as_view(), name="landing_page"),
    path("gene/", views.GeneViewSet.as_view({"post": "post", "get": "get"}), name="gene_query"),
    path("cell/", views.CellViewSet.as_view({"post": "post", "get": "get"}), name="cell_query"),
    path("organ/", views.OrganViewSet.as_view({"post": "post", "get": "get"}), name="organ_query"),
    path("protein/", views.ProteinViewSet.as_view({"get": "get"}), name="protein_query"),
    path("cluster/", views.ClusterViewSet.as_view({"post": "post", "get": "get"}), name="cluster_query"),
    path("geneform/", views.GeneQueryView.as_view(), name="gene_query_form"),
    path("cellform/", views.CellQueryView.as_view(), name="cell_query_form"),
    path("organform/", views.OrganQueryView.as_view(), name="organ_query_form"),
    path("clusterform/", views.ClusterQueryView.as_view(), name="cluster_query_form"),
    path("celllist/", views.CellListView.as_view(), name="cell_list"),
    path("genelist/", views.GeneListView.as_view(), name="gene_list"),
    path("clusterlist/", views.ClusterListView.as_view(), name="cluster_list"),
    path("organlist/", views.OrganListView.as_view(), name="organ_list"),
    path("allgenelist/", views.AllGeneListView.as_view(), name="all_gene_list"),
    path("allorganlist/", views.AllOrganListView.as_view(), name="all_organ_list"),
    path("allproteinlist/", views.AllProteinListView.as_view(), name="all_protein_list"),
    path("allclusterlist/", views.AllClusterListView.as_view(), name="all_cluster_list"),
    path(
        "openapi",
        get_schema_view(
            title="HuBMAP cell indexing",
            version="0.1-dev",
        ),
        name="openapi-schema",
    ),
]
