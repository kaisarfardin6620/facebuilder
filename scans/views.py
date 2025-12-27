from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import FaceScan, UserGoal
from .serializers import FaceScanSerializer, SetGoalsSerializer
from workouts.utils import generate_workout_plan
from payments.services import verify_subscription_status
from .ai_logic import analyze_face_image 
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

class ScanFaceView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60 * 1))
    @method_decorator(vary_on_headers('Authorization'))
    def get(self, request):
        scan = FaceScan.objects.filter(user=request.user).order_by('-created_at').first()
        if not scan:
            return Response({"message": "No scans found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer_data = FaceScanSerializer(scan, context={'request': request}).data
        return Response(serializer_data, status=status.HTTP_200_OK)

    def post(self, request):
        if 'image' not in request.FILES:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES['image']
        
        try:
            new_metrics = analyze_face_image(image_file)
            
            last_scan = FaceScan.objects.filter(
                user=request.user, 
                status='COMPLETED'
            ).exclude(jawline_angle__isnull=True).order_by('-created_at').first()
            
            final_jawline = new_metrics['jawline_angle']
            final_symmetry = new_metrics['symmetry_score']
            final_puffiness = new_metrics['puffiness_index']

            if last_scan:
                final_jawline = (final_jawline * 0.7) + (last_scan.jawline_angle * 0.3)
                final_symmetry = (final_symmetry * 0.7) + (last_scan.symmetry_score * 0.3)
                final_puffiness = (final_puffiness * 0.7) + (last_scan.puffiness_index * 0.3)

            image_file.seek(0)
            scan = FaceScan.objects.create(
                user=request.user,
                image=image_file,
                status='COMPLETED',
                jawline_angle=round(final_jawline, 1),
                symmetry_score=round(final_symmetry, 1),
                puffiness_index=round(final_puffiness, 2)
            )
            
            serializer_data = FaceScanSerializer(scan, context={'request': request}).data

            return Response({
                "message": "Scan complete.",
                "scan_data": serializer_data
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({"error": "Processing failed", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SetGoalsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SetGoalsSerializer(data=request.data)
        if serializer.is_valid():
            goal, _ = UserGoal.objects.get_or_create(user=request.user)
            goal.wants_sharper_jawline = serializer.data['wants_sharper_jawline']
            goal.wants_reduce_puffiness = serializer.data['wants_reduce_puffiness']
            goal.wants_improve_symmetry = serializer.data['wants_improve_symmetry']
            goal.save()

            latest_scan = FaceScan.objects.filter(user=request.user, status='COMPLETED').order_by('-created_at').first()
            
            if latest_scan:
                generate_workout_plan(request.user, latest_scan, goal)
                
                is_premium = verify_subscription_status(request.user)

                return Response({
                    "message": "Goals set and Plan generated.",
                    "is_premium": is_premium
                }, status=status.HTTP_200_OK)
            
            return Response({"error": "No completed scan found."}, status=status.HTTP_404_NOT_FOUND)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)