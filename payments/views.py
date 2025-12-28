from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from dashboard.models import Subscription, PaymentHistory
from datetime import datetime
from django.utils.decorators import method_decorator 
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .services import manual_sync_revenuecat, verify_subscription_status

User = get_user_model()

class TestRevenueCatConnection(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_active = verify_subscription_status(request.user)
        return Response({
            "message": "User has active Premium subscription." if is_active else "User does NOT have active subscription.",
            "is_premium": is_active
        }, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class RevenueCatWebhookView(APIView):
    authentication_classes = [] 
    permission_classes = [AllowAny]

    def post(self, request):
        auth_header = request.headers.get('Authorization')
        expected_token = f"Bearer {settings.REVENUECAT_WEBHOOK_SECRET}"
        
        if not settings.DEBUG and auth_header != expected_token:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        event = request.data.get('event', {})
        event_type = event.get('type')
        event_id = event.get('id')
        
        if event_type == 'TEST':
            return Response({"message": "Test event received successfully"}, status=status.HTTP_200_OK)

        app_user_id = event.get('app_user_id') 

        if not app_user_id:
            return Response({"message": "No user ID"}, status=status.HTTP_200_OK)

        try:
            user = User.objects.get(phone_number=app_user_id)
            
            if event_type in ['INITIAL_PURCHASE', 'RENEWAL', 'uncancellation', 'NON_RENEWING_PURCHASE']:
                expiry_time_ms = event.get('expiration_at_ms')
                product_id = event.get('product_id', 'Unknown')
                price_in_usd = event.get('price_in_usd') 
                
                expiry_date = None
                if expiry_time_ms:
                    expiry_date = datetime.fromtimestamp(expiry_time_ms / 1000.0)

                Subscription.objects.update_or_create(
                    user=user,
                    defaults={
                        'is_active': True,
                        'plan_name': product_id,
                        'expiry_date': expiry_date
                    }
                )

                amount = float(price_in_usd) if price_in_usd else 0.0

                if amount > 0:
                    if not PaymentHistory.objects.filter(transaction_id=event_id).exists():
                        PaymentHistory.objects.create(
                            user=user,
                            plan_name=product_id,
                            amount=amount,
                            transaction_id=event_id
                        )

            elif event_type in ['CANCELLATION', 'EXPIRATION', 'billing_issue']:
                Subscription.objects.filter(user=user).update(is_active=False)

            return Response({"message": "Webhook processed"}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"message": "User not found, ignoring"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SyncSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        is_premium = manual_sync_revenuecat(request.user)
        message = "Subscription synced. You are Premium." if is_premium else "Subscription synced. No active premium plan found."
        return Response({
            "message": message,
            "is_premium": is_premium
        }, status=status.HTTP_200_OK)