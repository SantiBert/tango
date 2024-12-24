from django_filters import rest_framework as filters
from django.db.models import Q
from .models import InversorTemporal

class InversorTemporalFilter(filters.FilterSet):
    search = filters.CharFilter(method='filter_by_name')

    class Meta:
        model = InversorTemporal
        fields = []

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value) | 
            Q(last_name__icontains=value)  | 
            Q(firm_name__icontains=value)  | 
            Q(email__icontains=value)
        )
