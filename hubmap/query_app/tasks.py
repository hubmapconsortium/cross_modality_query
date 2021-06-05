from datetime import datetime

from celery import shared_task
from django.conf import settings

from .models import QuerySet


@shared_task
def delete_expired_querysets():
    querysets = QuerySet.objects.filter(
        created__lt=datetime.now() - settings.QUERY_TOKEN_EXPIRATION
    )
    querysets.delete()
