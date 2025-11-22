from rest_framework import serializers
from .models import FaceScan, UserGoal

class FaceScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaceScan
        fields = ['id', 'image', 'jawline_angle', 'symmetry_score', 'puffiness_index', 'created_at']
        read_only_fields = ['jawline_angle', 'symmetry_score', 'puffiness_index', 'created_at']

class UserGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGoal
        fields = '__all__'