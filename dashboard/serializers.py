from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import Subscription
from scans.models import FaceScan, UserGoal
from scans.serializers import FaceScanSerializer, UserGoalSerializer
from workouts.models import WorkoutSession

User = get_user_model()

class AdminUserListSerializer(serializers.ModelSerializer):
    scans_count = serializers.SerializerMethodField()
    current_plan = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'phone_number', 'date_joined', 'is_active', 'scans_count', 'current_plan']

    def get_scans_count(self, obj):
        return FaceScan.objects.filter(user=obj).count()

    def get_current_plan(self, obj):
        sub = Subscription.objects.filter(user=obj, is_active=True).first()
        if sub:
            return sub.plan_name 
        return "Free"

class AdminUserDetailSerializer(serializers.ModelSerializer):
    scans = FaceScanSerializer(many=True, read_only=True)
    goals = UserGoalSerializer(read_only=True)
    total_sessions = serializers.SerializerMethodField()
    current_plan = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'name', 'phone_number', 'date_joined', 'is_active', 
            'total_sessions', 'current_plan', 'goals', 'scans'
        ]

    def get_total_sessions(self, obj):
        return WorkoutSession.objects.filter(user=obj).count()

    def get_current_plan(self, obj):
        sub = Subscription.objects.filter(user=obj, is_active=True).first()
        return sub.plan_name if sub else "Free"

class AdminProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['name', 'phone_number', 'profile_picture']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.profile_picture:
            image_url = instance.profile_picture.url
            if not image_url.startswith('http'):
                representation['profile_picture'] = f"{settings.SERVER_BASE_URL}{image_url}"
        return representation

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()