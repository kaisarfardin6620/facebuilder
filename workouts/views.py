from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import WorkoutPlan, WorkoutSession
from .serializers import WorkoutPlanSerializer
from scans.models import FaceScan, UserGoal
from scans.serializers import FaceScanSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime
from payments.services import verify_subscription_status
from .utils import update_plan_difficulty

User = get_user_model()

class MyPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_premium = verify_subscription_status(request.user)
        if not is_premium:
            return Response({
                "error": "PAYMENT_REQUIRED",
                "message": "You must subscribe to view your personalized plan."
            }, status=status.HTTP_402_PAYMENT_REQUIRED) 

        try:
            plan = WorkoutPlan.objects.select_related('user').get(user=request.user, is_active=True)
            serializer_data = WorkoutPlanSerializer(plan).data
            return Response(serializer_data, status=status.HTTP_200_OK)
        except WorkoutPlan.DoesNotExist:
            return Response({"message": "No active plan found. Set goals first."}, status=status.HTTP_404_NOT_FOUND)

class CompleteSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        is_premium = verify_subscription_status(request.user)
        if not is_premium:
            return Response({"error": "PAYMENT_REQUIRED"}, status=status.HTTP_402_PAYMENT_REQUIRED)

        WorkoutSession.objects.create(user=request.user)
        
        plan = WorkoutPlan.objects.filter(user=request.user, is_active=True).first()
        if plan:
            plan.sessions_completed_count += 1
            
            if plan.sessions_completed_count % 7 == 0:
                plan.difficulty_level += 1
                update_plan_difficulty(plan)
            
            plan.save()
            
        return Response({"message": "Session completed!"}, status=status.HTTP_200_OK)

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_premium = verify_subscription_status(request.user)
        if not is_premium:
            return Response({"error": "PAYMENT_REQUIRED"}, status=status.HTTP_402_PAYMENT_REQUIRED)

        user = request.user

        sessions_dates = list(
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

        scans_list = list(FaceScan.objects.filter(user=user).order_by('created_at'))
        scan_data = FaceScanSerializer(scans_list, many=True).data
        
        latest_scan = scans_list[-1] if scans_list else None
        first_scan = scans_list[0] if scans_list else None
        goal = UserGoal.objects.filter(user=user).first()
        
        progress_summary = {
            "overall_progress": 0,
            "jawline_status": "Pending",
            "goals_hit": []
        }

        comparison_text = "Analysis pending more data."
        consistency_text = "Consistency shapes results."
        next_badge_days = 7 - (streak % 7) if streak > 0 else 7

        if streak == 0:
            consistency_text = "The best time to start is now. Let's do this!"
        elif streak <= 3:
            consistency_text = "Momentum is building! Keep this streak alive."
        elif streak < 7:
            consistency_text = "You are forming a powerful habit. Great work!"
        else:
            consistency_text = "Unstoppable! Your consistency is in the top 1%."

        if latest_scan and goal and latest_scan.status == 'COMPLETED':
            current_val = latest_scan.jawline_angle if latest_scan.jawline_angle is not None else 0
            target_val = goal.target_jawline if goal.target_jawline is not None else 0
            
            progress_summary['jawline_status'] = f"{int(current_val)}° (Goal {int(target_val)}°)"
            
            start_val = first_scan.jawline_angle if (first_scan and first_scan.jawline_angle) else current_val
            
            total_journey = start_val - target_val
            made_journey = start_val - current_val
            
            percent_complete = 0
            if abs(total_journey) > 0.1: 
                percent_complete = (made_journey / total_journey) * 100
                percent_complete = max(0, min(100, percent_complete))
            else:
                percent_complete = 100 if current_val <= target_val else 0

            progress_summary['overall_progress'] = int(percent_complete)
            
            progress_summary['goals_hit'].append({
                "title": "Sharper Jawline",
                "status": f"{int(percent_complete)}% complete",
                "target": f"Goal {int(target_val)}°"
            })
            
            if streak >= 7:
                 progress_summary['goals_hit'].append({
                    "title": "Consistency Master",
                    "status": "On Track",
                    "target": "Keep going"
                })

            if first_scan and latest_scan:
                if first_scan.id == latest_scan.id:
                    comparison_text = "Baseline established. Your next scan will reveal your progress."
                else:
                    diff = start_val - current_val
                    if diff > 0.5:
                        imp_score = (diff / start_val) * 100 * 4 
                        comparison_text = f"Your face is {int(imp_score)}% more defined than your first scan - keep it up!"
                    elif diff > -0.5:
                         comparison_text = "You are maintaining your baseline perfectly. Increase intensity for more definition."
                    else:
                         comparison_text = "Slight regression detected. Focus on posture and tongue position during exercises."

        badges = []
        if streak > 0:
            badges.append(f"Day {streak} Complete")
        
        sym_score = 0
        if latest_scan and latest_scan.symmetry_score:
            sym_score = int(latest_scan.symmetry_score)

        user_score = (streak * 10) + sym_score
        
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
            "next_badge_in_days": next_badge_days,
            "consistency_text": consistency_text,
            "comparison_text": comparison_text,
            "graph_data": scan_data,
            "progress_summary": progress_summary, 
            "leaderboard": leaderboard_data,      
            "badges": badges 
        }, status=status.HTTP_200_OK)