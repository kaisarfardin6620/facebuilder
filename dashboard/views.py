from tokenize import TokenError
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from .models import Subscription, PaymentHistory
from .serializers import *
from scans.models import FaceScan
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.serializers import LoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from authentication.utils import send_otp_via_twilio, verify_otp_via_twilio
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

User = get_user_model()

def get_tokens_for_admin(user):
    refresh = RefreshToken.for_user(user)
    refresh['is_admin'] = True
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class DashboardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class AdminLoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.data['phone_number']
        password = serializer.data['password']

        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return Response({"error": "Wrong password."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_staff:
            return Response(
                {"error": "Access Denied. You do not have admin privileges."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        tokens = get_tokens_for_admin(user)

        return Response({
            "message": "Admin Login Successful",
            "token": tokens['access'],
            "refresh_token": tokens['refresh'],
            "admin_name": user.name
        }, status=status.HTTP_200_OK)

class AdminForgotPasswordView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.data['phone_number']
            try:
                user = User.objects.get(phone_number=phone)
                
                if not user.is_staff:
                    return Response({"error": "Access Denied. Not an admin account."}, status=status.HTTP_403_FORBIDDEN)
                
                if send_otp_via_twilio(phone):
                    return Response({"message": "OTP sent to admin number."}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Failed to send SMS."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            except User.DoesNotExist:
                return Response({"error": "Admin user not found"}, status=status.HTTP_404_NOT_FOUND)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminResetPasswordConfirmView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.data['phone_number']
            otp = serializer.data['otp']
            new_pass = serializer.data['new_password']

            if verify_otp_via_twilio(phone, otp):
                try:
                    user = User.objects.get(phone_number=phone)
                    
                    if not user.is_staff:
                        return Response({"error": "Access Denied."}, status=status.HTTP_403_FORBIDDEN)

                    user.set_password(new_pass)
                    user.save()
                    return Response({"message": "Admin password changed successfully."}, status=status.HTTP_200_OK)
                except User.DoesNotExist:
                    return Response({"error": "User error"}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DashboardStatsView(APIView):
    permission_classes = [IsAdminUser]

    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_headers('Authorization'))
    def get(self, request):
        total_users = User.objects.filter(is_staff=False).count()
        total_scans = FaceScan.objects.count()
        
        earnings_agg = PaymentHistory.objects.aggregate(total=Sum('amount'))
        total_earnings = earnings_agg['total'] if earnings_agg['total'] else 0.00

        raw_graph = list(PaymentHistory.objects.annotate(month=TruncMonth('transaction_date')) \
            .values('month') \
            .annotate(amount=Sum('amount')) \
            .order_by('month'))
        
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

class AdminProfileView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        serializer = AdminProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = AdminProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminChangePasswordView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            is_correct = user.check_password(serializer.data.get("old_password"))
            
            if not is_correct:
                return Response({"error": "Wrong old password"}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.data.get("new_password"))
            user.save()
            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            try:
                refresh_token = serializer.data['refresh']
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
            except TokenError as e:
                return Response({"error": f"Token Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)