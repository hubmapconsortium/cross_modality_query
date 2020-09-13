from django.contrib import admin
from django.urls import path

from . import views

admin.autodiscover()
# first we define the serializers

urlpatterns = [
    path('genequery/', views.GeneViewSet.as_view({'post': 'post'}), name="gene_query"),
    path('cellquery/', views.CellViewSet.as_view({'post': 'post'}), name="cell_query"),
    path('groupquery/', views.Cell_GroupingViewSet.as_view({'post': 'post'}), name="group_query"),
    path('query/', views.LandingFormView, name="landing_page"),
    path('genequeryform', views.GeneQueryView, name="gene_query_form"),
    path('cellqueryform', views.CellQueryView, name="cell_query_form"),
    path('organqueryform', views.OrganQueryView, name="organ_query_form"),
]
