from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SubscriptionPlan
from scans.models import FaceScan

User = get_user_model()

class AdminUserListSerializer(serializers.ModelSerializer):
    scans_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'phone_number', 'date_joined', 'is_active', 'scans_count']

    def get_scans_count(self, obj):
        return FaceScan.objects.filter(user=obj).count()

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class AdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'phone_number']

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)