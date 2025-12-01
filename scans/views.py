from adrf.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from asgiref.sync import sync_to_async
from .models import FaceScan, UserGoal
from .serializers import FaceScanSerializer, SetGoalsSerializer
from .ai_logic import analyze_face_image
from workouts.utils import generate_workout_plan
from payments.services import verify_subscription_status

analyze_face_async = sync_to_async(analyze_face_image, thread_sensitive=False)
generate_plan_async = sync_to_async(generate_workout_plan)

class ScanFaceView(APIView):
    permission_classes = [IsAuthenticated]

    async def post(self, request):
        if 'image' not in request.FILES:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES['image']
        
        try:
            # 1. Run AI (Free for everyone - The Hook)
            metrics = await analyze_face_async(image_file)
            image_file.seek(0) 

            scan = await FaceScan.objects.acreate(
                user=request.user,
                image=image_file,
                jawline_angle=metrics['jawline_angle'],
                symmetry_score=metrics['symmetry_score'],
                puffiness_index=metrics['puffiness_index']
            )
            
            await UserGoal.objects.aupdate_or_create(
                user=request.user,
                defaults={
                    'target_jawline': round(metrics['jawline_angle'] * 0.95, 1),
                    'target_symmetry': min(100, round(metrics['symmetry_score'] * 1.10, 1)),
                    'target_puffiness': round(metrics['puffiness_index'] * 0.90, 2)
                }
            )
            
            serializer = FaceScanSerializer(scan)
            
            # Return Full Data (No locks here)
            return Response({
                "message": "Scan complete. Please set goals.",
                "scan_data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Processing failed", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SetGoalsView(APIView):
    permission_classes = [IsAuthenticated]

    async def post(self, request):
        serializer = SetGoalsSerializer(data=request.data)
        if serializer.is_valid():
            # 1. Save User Preferences
            goal, _ = await UserGoal.objects.aget_or_create(user=request.user)
            goal.wants_sharper_jawline = serializer.data['wants_sharper_jawline']
            goal.wants_reduce_puffiness = serializer.data['wants_reduce_puffiness']
            goal.wants_improve_symmetry = serializer.data['wants_improve_symmetry']
            await goal.asave()

            # 2. Generate Plan (We create it even for free users, but they can't access it yet)
            latest_scan = await FaceScan.objects.filter(user=request.user).alast()
            if latest_scan:
                await generate_plan_async(request.user, latest_scan, goal)
                
                # 3. CHECK PAYMENT STATUS NOW
                is_premium = await verify_subscription_status(request.user)

                return Response({
                    "message": "Goals set and Plan generated.",
                    "is_premium": is_premium # <--- Frontend Logic: If False -> Redirect to Paywall
                }, status=status.HTTP_200_OK)
            
            return Response({"error": "No scan found"}, status=status.HTTP_404_NOT_FOUND)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)