from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

admin.autodiscover()
# first we define the serializers

urlpatterns = [
    path('genequery/', views.GeneViewSet.as_view(), name="gene_query"),
    path('cellquery/', views.CellViewSet.as_view(), name="cell_query"),
    path('groupquery/', views.Cell_GroupingViewSet.as_view(), name="group_query"),
    path('genes/', views.GeneListView.as_view(), name="genes"),
]
