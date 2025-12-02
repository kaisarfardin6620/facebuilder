from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SubscriptionPlan, Subscription
from scans.models import FaceScan, UserGoal
from scans.serializers import FaceScanSerializer, UserGoalSerializer
from workouts.models import WorkoutSession

User = get_user_model()

class AdminUserListSerializer(serializers.ModelSerializer):
    """ Lightweight serializer for the Table View """
    scans_count = serializers.SerializerMethodField()
    current_plan = serializers.SerializerMethodField() # <--- NEW FIELD

    class Meta:
        model = User
        fields = ['id', 'name', 'phone_number', 'date_joined', 'is_active', 'scans_count', 'current_plan']

    def get_scans_count(self, obj):
        return FaceScan.objects.filter(user=obj).count()

    def get_current_plan(self, obj):
        # Fetch the active subscription for this user
        sub = Subscription.objects.filter(user=obj, is_active=True).first()
        if sub:
            # Return "Monthly", "Yearly" etc based on product ID
            return sub.plan_name 
        return "Free"

# ... (Keep AdminUserDetailSerializer, SubscriptionPlanSerializer, etc. exactly as they were) ...
# ... Just copy the rest of the file below ...
class AdminUserDetailSerializer(serializers.ModelSerializer):
    scans = FaceScanSerializer(many=True, read_only=True)
    goals = UserGoalSerializer(read_only=True)
    total_sessions = serializers.SerializerMethodField()
    current_plan = serializers.SerializerMethodField() # <--- Added here too

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