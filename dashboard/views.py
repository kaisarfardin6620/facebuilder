from adrf.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate
from .models import SubscriptionPlan
from .serializers import *
from scans.models import FaceScan
from asgiref.sync import sync_to_async
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.serializers import LoginSerializer
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
            return Response({"error": "User not found. Please enter a valid phone number."}, status=status.HTTP_404_NOT_FOUND)

        is_correct = await sync_to_async(user.check_password)(password)
        if not is_correct:
            return Response({"error": "Wrong password. Please enter the correct password."}, status=status.HTTP_401_UNAUTHORIZED)

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

class DashboardStatsView(APIView):
    permission_classes = [IsAdminUser]

    async def get(self, request):
        total_users = await User.objects.filter(is_staff=False).acount()
        total_scans = await FaceScan.objects.acount()
        
        total_earnings = 52567.53 

        def get_graph_data():
            return list(FaceScan.objects.annotate(date=TruncDate('created_at')) \
                .values('date') \
                .annotate(count=Count('id')) \
                .order_by('date'))

        scan_graph = await sync_to_async(get_graph_data)()

        return Response({
            "cards": {
                "total_users": total_users,
                "total_earnings": total_earnings,
                "total_scans": total_scans
            },
            "graph_data": scan_graph
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