from rest_framework import serializers
from cities_light.models import City

class LocationSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField(method_name="get_location")
    
    def get_location(self, obj):
        return obj.display_name
    
    class Meta:
        model = City
        fields = ['location']