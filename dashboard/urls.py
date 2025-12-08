from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'users', UserManagementViewSet, basename='admin-users')

urlpatterns = [
    path('login/', AdminLoginView.as_view(), name='admin-login'),
    path('stats/', DashboardStatsView.as_view(), name='admin-stats'),
    path('profile/', AdminProfileView.as_view(), name='admin-profile'),
    path('change-password/', AdminChangePasswordView.as_view(), name='admin-password'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', include(router.urls)),
]