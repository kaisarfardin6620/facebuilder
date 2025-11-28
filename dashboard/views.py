from rest_framework.views import APIView
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate
from .models import SubscriptionPlan
from .serializers import *
from scans.models import FaceScan

User = get_user_model()

class DashboardStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_users = User.objects.filter(is_staff=False).count()
        total_scans = FaceScan.objects.count()
        
        total_earnings = 52567.53 

        scan_graph = FaceScan.objects.annotate(date=TruncDate('created_at')) \
            .values('date') \
            .annotate(count=Count('id')) \
            .order_by('date')

        return Response({
            "cards": {
                "total_users": total_users,
                "total_earnings": total_earnings,
                "total_scans": total_scans
            },
            "graph_data": scan_graph
        })


class UserManagementViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = User.objects.filter(is_staff=False).order_by('-date_joined')
    serializer_class = AdminUserListSerializer
    http_method_names = ['get', 'delete']

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = SubscriptionPlan.objects.all().order_by('-created_at')
    serializer_class = SubscriptionPlanSerializer

class AdminProfileView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = AdminProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminChangePasswordView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.data.get("old_password")):
                return Response({"error": "Wrong old password"}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.data.get("new_password"))
            user.save()
            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)