from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SubscriptionPlan
from scans.models import FaceScan, UserGoal
from scans.serializers import FaceScanSerializer, UserGoalSerializer
from workouts.models import WorkoutSession

User = get_user_model()

class AdminUserListSerializer(serializers.ModelSerializer):
    """ Lightweight serializer for the Table View """
    scans_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'phone_number', 'date_joined', 'is_active', 'scans_count']

    def get_scans_count(self, obj):
        return FaceScan.objects.filter(user=obj).count()

class AdminUserDetailSerializer(serializers.ModelSerializer):
    """ Heavy serializer for the Detail View (Profile + Scans + Goals) """
    scans = FaceScanSerializer(many=True, read_only=True)
    goals = UserGoalSerializer(read_only=True)
    total_sessions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'name', 'phone_number', 'date_joined', 'is_active', 
            'total_sessions', 'goals', 'scans'
        ]

    def get_total_sessions(self, obj):
        return WorkoutSession.objects.filter(user=obj).count()

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class AdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'phone_number', 'profile_picture']

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)