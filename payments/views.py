from adrf.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from dashboard.models import Subscription
from datetime import datetime
from .services import verify_subscription_status

User = get_user_model()

class TestRevenueCatConnection(APIView):
    permission_classes = [IsAuthenticated]

    async def get(self, request):
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

class RevenueCatWebhookView(APIView):
    # Security: Allow RevenueCat to hit this without a JWT token
    authentication_classes = [] 
    permission_classes = [AllowAny]

    async def post(self, request):
        event = request.data.get('event', {})
        event_type = event.get('type')
        
        # RevenueCat sends the User's Phone Number as 'app_user_id'
        app_user_id = event.get('app_user_id') 

        if not app_user_id:
            return Response({"message": "No user ID"}, status=status.HTTP_200_OK)

        try:
            # Find the user by phone number
            user = await User.objects.aget(phone_number=app_user_id)
            
            # 1. Handle Purchase / Renewal
            if event_type in ['INITIAL_PURCHASE', 'RENEWAL', 'uncancellation', 'NON_RENEWING_PURCHASE']:
                expiry_time_ms = event.get('expiration_at_ms')
                product_id = event.get('product_id', 'Unknown')
                
                expiry_date = None
                if expiry_time_ms:
                    expiry_date = datetime.fromtimestamp(expiry_time_ms / 1000.0)

                await Subscription.objects.aupdate_or_create(
                    user=user,
                    defaults={
                        'is_active': True,
                        'plan_name': product_id,
                        'expiry_date': expiry_date
                    }
                )

            # 2. Handle Cancellation / Expiration
            elif event_type in ['CANCELLATION', 'EXPIRATION', 'billing_issue']:
                try:
                    sub = await Subscription.objects.aget(user=user)
                    sub.is_active = False
                    await sub.asave()
                except Subscription.DoesNotExist:
                    pass

            return Response({"message": "Webhook processed"}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            # RevenueCat might send test events with fake IDs, just ignore them
            return Response({"message": "User not found in Django"}, status=status.HTTP_200_OK)