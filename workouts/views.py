from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import WorkoutPlan, WorkoutSession
from .serializers import WorkoutPlanSerializer
from scans.models import FaceScan
from scans.serializers import FaceScanSerializer

class MyPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            plan = WorkoutPlan.objects.get(user=request.user, is_active=True)
            serializer = WorkoutPlanSerializer(plan)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except WorkoutPlan.DoesNotExist:
            return Response({"message": "No active plan found. Please set goals first."}, status=status.HTTP_404_NOT_FOUND)

class CompleteSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        WorkoutSession.objects.create(user=request.user)
        
        plan = WorkoutPlan.objects.filter(user=request.user, is_active=True).first()
        if plan:
            plan.sessions_completed_count += 1
            plan.save()
            
        return Response({"message": "Session completed! Streak updated."}, status=status.HTTP_200_OK)

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_sessions = WorkoutSession.objects.filter(user=request.user).count()
        
        scans = FaceScan.objects.filter(user=request.user).order_by('created_at')
        scan_data = FaceScanSerializer(scans, many=True).data
        
        return Response({
            "streak_days": total_sessions,
            "graph_data": scan_data,
            "badges": ["Day 1 Complete"] if total_sessions >= 1 else []
        }, status=status.HTTP_200_OK)