from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from dashboard.models import Subscription, PaymentHistory
from datetime import datetime
from django.utils.decorators import method_decorator 
from django.views.decorators.csrf import csrf_exempt
from .services import manual_sync_revenuecat, verify_subscription_status

User = get_user_model()

class TestRevenueCatConnection(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_active = verify_subscription_status(request.user)

        if is_active:
            return Response({
                "message": "User has active Premium subscription.",
                "is_premium": True
            }, status=status.HTTP_200_OK)
        
        return Response({
            "message": "User does NOT have active subscription.",
            "is_premium": False
        }, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class RevenueCatWebhookView(APIView):
    authentication_classes = [] 
    permission_classes = [AllowAny]

    def post(self, request):
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
                try:
                    sub = Subscription.objects.get(user=user)
                    sub.is_active = False
                    sub.save()
                except Subscription.DoesNotExist:
                    pass

            return Response({"message": "Webhook processed"}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"message": "User not found, ignoring"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Webhook Error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SyncSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        is_premium = manual_sync_revenuecat(request.user)
        
        if is_premium:
            return Response({
                "message": "Subscription synced. You are Premium.",
                "is_premium": True
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "Subscription synced. No active premium plan found.",
                "is_premium": False
            }, status=status.HTTP_200_OK)