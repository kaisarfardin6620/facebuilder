from adrf.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import WorkoutPlan, WorkoutSession
from .serializers import WorkoutPlanSerializer
from scans.models import FaceScan, UserGoal
from scans.serializers import FaceScanSerializer
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime
from payments.services import verify_subscription_status

User = get_user_model()

class MyPlanView(APIView):
    permission_classes = [IsAuthenticated]

    async def get(self, request):
        # 1. BARRIER: Check Payment
        is_premium = await verify_subscription_status(request.user)
        if not is_premium:
            return Response({
                "error": "PAYMENT_REQUIRED",
                "message": "You must subscribe to view your personalized plan."
            }, status=status.HTTP_402_PAYMENT_REQUIRED) # 402 is specific for Payment

        try:
            plan = await WorkoutPlan.objects.select_related('user').aget(user=request.user, is_active=True)
            serializer_data = await sync_to_async(lambda: WorkoutPlanSerializer(plan).data)()
            return Response(serializer_data, status=status.HTTP_200_OK)
        except WorkoutPlan.DoesNotExist:
            return Response({"message": "No active plan found. Set goals first."}, status=status.HTTP_404_NOT_FOUND)

class CompleteSessionView(APIView):
    permission_classes = [IsAuthenticated]

    async def post(self, request):
        # 1. BARRIER
        is_premium = await verify_subscription_status(request.user)
        if not is_premium:
            return Response({"error": "PAYMENT_REQUIRED"}, status=status.HTTP_402_PAYMENT_REQUIRED)

        await WorkoutSession.objects.acreate(user=request.user)
        
        plan = await WorkoutPlan.objects.filter(user=request.user, is_active=True).afirst()
        if plan:
            plan.sessions_completed_count += 1
            await plan.asave()
            
        return Response({"message": "Session completed!"}, status=status.HTTP_200_OK)

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    async def get(self, request):
        # 1. BARRIER
        is_premium = await verify_subscription_status(request.user)
        if not is_premium:
            return Response({"error": "PAYMENT_REQUIRED"}, status=status.HTTP_402_PAYMENT_REQUIRED)

        user = request.user

        sessions_dates = await sync_to_async(list)(
            WorkoutSession.objects.filter(user=user)
            .values_list('date_completed__date', flat=True)
            .distinct()
            .order_by('-date_completed__date')
        )

        streak = 0
        if sessions_dates:
            today = timezone.now().date()
            latest_session = sessions_dates[0]

            if latest_session == today or latest_session == today - datetime.timedelta(days=1):
                streak = 1
                for i in range(len(sessions_dates) - 1):
                    current_date = sessions_dates[i]
                    previous_date = sessions_dates[i+1]
                    
                    if current_date - previous_date == datetime.timedelta(days=1):
                        streak += 1
                    else:
                        break
            else:
                streak = 0

        scans_qs = FaceScan.objects.filter(user=user).order_by('created_at')
        scans_list = []
        async for scan in scans_qs:
            scans_list.append(scan)
        
        scan_data = await sync_to_async(lambda: FaceScanSerializer(scans_list, many=True).data)()
        
        latest_scan = scans_list[-1] if scans_list else None
        goal = await UserGoal.objects.filter(user=user).afirst()
        
        progress_summary = {
            "overall_progress": 0,
            "jawline_status": "Pending",
            "goals_hit": []
        }

        if latest_scan and goal:
            jaw_diff = latest_scan.jawline_angle - goal.target_jawline
            is_jaw_hit = jaw_diff <= 2
            
            progress_summary['jawline_status'] = "100% complete" if is_jaw_hit else f"{int(latest_scan.jawline_angle)}° (Goal {int(goal.target_jawline)}°)"
            progress_summary['overall_progress'] = 95 if is_jaw_hit else 50 
            
            if is_jaw_hit:
                progress_summary['goals_hit'].append("Sharper Jawline")

        badges = []
        if streak > 0:
            badges.append(f"Day {streak} Complete")
        
        user_score = (streak * 10) + (int(latest_scan.symmetry_score) if latest_scan else 0)
        
        leaderboard_data = {
            "your_rank": "#3",
            "your_score": user_score,
            "competitors": [
                {"rank": "#1", "name": "Last Week", "score": user_score + 50, "trend": "+145"},
                {"rank": "#2", "name": "Best Week", "score": user_score + 20, "trend": "+0"},
                {"rank": "#3", "name": "You", "score": user_score, "trend": f"+{streak}"},
            ]
        }

        return Response({
            "streak_days": streak,
            "graph_data": scan_data,
            "progress_summary": progress_summary, 
            "leaderboard": leaderboard_data,      
            "badges": badges 
        }, status=status.HTTP_200_OK)