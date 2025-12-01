from adrf.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .services import verify_subscription_status

class TestRevenueCatConnection(APIView):
    permission_classes = [IsAuthenticated]

    async def get(self, request):
        # Calls the new service logic
        is_active = await verify_subscription_status(request.user)

        if is_active:
            return Response({
                "message": "User has active Premium subscription.",
                "is_premium": True
            }, status=status.HTTP_200_OK)
        
        return Response({
            "message": "User does NOT have active subscription.",
            "is_premium": False
        }, status=status.HTTP_200_OK)