from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, VerifyOTPView, LoginView, ForgotPasswordView, ResetPasswordConfirmView, ResendOTPView, LogoutView

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordConfirmView.as_view(), name='reset-password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]