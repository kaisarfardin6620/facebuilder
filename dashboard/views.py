from adrf.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from .models import SubscriptionPlan, Subscription, PaymentHistory
from .serializers import *
from scans.models import FaceScan
from asgiref.sync import sync_to_async
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.serializers import LoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from authentication.utils import send_otp_via_twilio, verify_otp_via_twilio
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter

User = get_user_model()

@sync_to_async
def get_tokens_for_admin(user):
    refresh = RefreshToken.for_user(user)
    refresh['is_admin'] = True
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

send_otp_async = sync_to_async(send_otp_via_twilio, thread_sensitive=False)
verify_otp_async = sync_to_async(verify_otp_via_twilio, thread_sensitive=False)

class DashboardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class AdminLoginView(APIView):
    async def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.data['phone_number']
        password = serializer.data['password']

        try:
            user = await User.objects.aget(phone_number=phone)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        is_correct = await sync_to_async(user.check_password)(password)
        if not is_correct:
            return Response({"error": "Wrong password."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_staff:
            return Response(
                {"error": "Access Denied. You do not have admin privileges."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        tokens = await get_tokens_for_admin(user)

        return Response({
            "message": "Admin Login Successful",
            "token": tokens['access'],
            "refresh_token": tokens['refresh'],
            "admin_name": user.name
        }, status=status.HTTP_200_OK)

class AdminForgotPasswordView(APIView):
    permission_classes = []

    async def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if await sync_to_async(serializer.is_valid)():
            phone = serializer.data['phone_number']
            try:
                user = await User.objects.aget(phone_number=phone)
                
                if not user.is_staff:
                    return Response({"error": "Access Denied. Not an admin account."}, status=status.HTTP_403_FORBIDDEN)
                
                if await send_otp_async(phone):
                    return Response({"message": "OTP sent to admin number."}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Failed to send SMS."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            except User.DoesNotExist:
                return Response({"error": "Admin user not found"}, status=status.HTTP_404_NOT_FOUND)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminResetPasswordConfirmView(APIView):
    permission_classes = []

    async def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if await sync_to_async(serializer.is_valid)():
            phone = serializer.data['phone_number']
            otp = serializer.data['otp']
            new_pass = serializer.data['new_password']

            if await verify_otp_async(phone, otp):
                try:
                    user = await User.objects.aget(phone_number=phone)
                    
                    if not user.is_staff:
                        return Response({"error": "Access Denied."}, status=status.HTTP_403_FORBIDDEN)

                    user.set_password(new_pass)
                    await user.asave()
                    return Response({"message": "Admin password changed successfully."}, status=status.HTTP_200_OK)
                except User.DoesNotExist:
                    return Response({"error": "User error"}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DashboardStatsView(APIView):
    permission_classes = [IsAdminUser]

    async def get(self, request):
        total_users = await User.objects.filter(is_staff=False).acount()
        total_scans = await FaceScan.objects.acount()
        
        earnings_agg = await PaymentHistory.objects.aaggregate(total=Sum('amount'))
        total_earnings = earnings_agg['total'] if earnings_agg['total'] else 0.00

        def get_earnings_graph():
            return list(PaymentHistory.objects.annotate(month=TruncMonth('transaction_date')) \
                .values('month') \
                .annotate(amount=Sum('amount')) \
                .order_by('month'))

        raw_graph = await sync_to_async(get_earnings_graph)()
        
        formatted_graph = []
        for entry in raw_graph:
            if entry['month']:
                formatted_graph.append({
                    "date": entry['month'].strftime("%Y-%m"),
                    "amount": float(entry['amount'])
                })

        return Response({
            "cards": {
                "total_users": total_users,
                "total_earnings": float(total_earnings),
                "total_scans": total_scans
            },
            "graph_data": formatted_graph
        })

class UserManagementViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = User.objects.filter(is_staff=False).order_by('-date_joined')
    http_method_names = ['get', 'delete', 'head', 'options']
    
    pagination_class = DashboardPagination
    filter_backends = [SearchFilter]
    search_fields = ['name', 'phone_number']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminUserDetailSerializer
        return AdminUserListSerializer

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = SubscriptionPlan.objects.all().order_by('-created_at')
    serializer_class = SubscriptionPlanSerializer
    pagination_class = DashboardPagination

class AdminProfileView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    async def get(self, request):
        serializer = AdminProfileSerializer(request.user)
        return Response(serializer.data)

    async def put(self, request):
        serializer = AdminProfileSerializer(request.user, data=request.data, partial=True)
        is_valid = await sync_to_async(serializer.is_valid)()
        if is_valid:
            await sync_to_async(serializer.save)()
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminChangePasswordView(APIView):
    permission_classes = [IsAdminUser]

    async def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            is_correct = await sync_to_async(user.check_password)(serializer.data.get("old_password"))
            
            if not is_correct:
                return Response({"error": "Wrong old password"}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.data.get("new_password"))
            await user.asave()
            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)