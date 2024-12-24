from rest_framework import serializers

class TrackEventSerializer(serializers.Serializer):
    event_name = serializers.CharField(max_length=255)
    distinct_id = serializers.CharField(max_length=255, default='anonymous')
    properties = serializers.DictField(required=False)