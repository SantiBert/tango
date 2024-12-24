from rest_framework import generics
from django_filters import rest_framework as filters

from cities_light.models import City
from .serializers import LocationSerializer
from .filters import CityFilter

from users.permissions import IsRegistered

class LocationListView(generics.ListAPIView):
    permission_classes =  [IsRegistered]
    queryset = City.objects.all()
    serializer_class = LocationSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = CityFilter

