from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import WorkoutPlan
from .serializers import WorkoutPlanSerializer

class MyPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the current active plan
        try:
            plan = WorkoutPlan.objects.get(user=request.user, is_active=True)
            serializer = WorkoutPlanSerializer(plan)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except WorkoutPlan.DoesNotExist:
            return Response({"message": "No active plan found. Please scan your face first."}, status=status.HTTP_404_NOT_FOUND)