from django.http import Http404
from django.shortcuts import get_object_or_404


def get_object_or_none(klass, *args, **kwargs):
    try:
        return get_object_or_404(klass, *args, **kwargs)
    except Http404:
        return None

ELEMENTS_PER_PAGE = 10

CACHE_SECONDS = 20
