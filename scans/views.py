from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import FaceScan, UserGoal
from .serializers import FaceScanSerializer, UserGoalSerializer
from .ai_logic import analyze_face_image
from workouts.utils import generate_workout_plan

class ScanFaceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'image' not in request.FILES:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES['image']
        
        try:
            # 1. Run AI Logic
            metrics = analyze_face_image(image_file)
            image_file.seek(0) 

            # 2. Save Scan
            scan = FaceScan.objects.create(
                user=request.user,
                image=image_file,
                jawline_angle=metrics['jawline_angle'],
                symmetry_score=metrics['symmetry_score'],
                puffiness_index=metrics['puffiness_index']
            )
            
            # 3. Create Goals
            UserGoal.objects.update_or_create(
                user=request.user,
                defaults={
                    'target_jawline': round(metrics['jawline_angle'] * 0.95, 1),
                    'target_symmetry': min(100, round(metrics['symmetry_score'] * 1.10, 1)),
                    'target_puffiness': round(metrics['puffiness_index'] * 0.90, 2)
                }
            )

            # 4. GENERATE WORKOUT PLAN (New Step)
            generate_workout_plan(request.user, scan)

            serializer = FaceScanSerializer(scan)
            
            return Response({
                "message": "Scan complete & Workout Plan Generated",
                "scan_data": serializer.data,
                "goals": {
                    "jawline": round(metrics['jawline_angle'] * 0.95, 1),
                    "symmetry": min(100, round(metrics['symmetry_score'] * 1.10, 1)),
                    "puffiness": round(metrics['puffiness_index'] * 0.90, 2)
                }
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Processing failed", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)