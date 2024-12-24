import django_filters
from cities_light.models import City

class CityFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='search_names', lookup_expr='icontains')

    class Meta:
        model = City
        fields = ['name']