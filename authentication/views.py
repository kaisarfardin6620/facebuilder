from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from .models import OneTimePassword, User
from .utils import send_otp_via_twilio
import random
from rest_framework.throttling import AnonRateThrottle

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def generate_and_send_otp(phone):
    otp_code = str(random.randint(1000, 9999))
    OneTimePassword.objects.update_or_create(
        phone_number=phone,
        defaults={'otp': otp_code}
    )
    return send_otp_via_twilio(phone, otp_code)

# Throttle for OTP endpoints
class OTPThrottle(AnonRateThrottle):
    scope = 'otp'

class LoginView(APIView):
    throttle_classes = [OTPThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.data['phone_number']
        password = serializer.data['password']

        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            return Response({"error": "Number incorrect, please provide valid number"}, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return Response({"error": "Wrong password, please enter correct password"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({"error": "Account not active. Please verify OTP first."}, status=status.HTTP_403_FORBIDDEN)

        tokens = get_tokens_for_user(user)

        return Response({
            "message": "Successfully Logged in.",
            "token": tokens['access'],
            "refresh_token": tokens['refresh']
        }, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    throttle_classes = [OTPThrottle]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.data['phone_number']
            otp_input = serializer.data['otp']
            try:
                otp_record = OneTimePassword.objects.get(phone_number=phone, otp=otp_input)
                user = User.objects.get(phone_number=phone)
                user.is_active = True
                user.save()
                otp_record.delete()

                tokens = get_tokens_for_user(user)

                return Response({
                    "message": "Verification Successful",
                    "token": tokens['access'],
                    "refresh_token": tokens['refresh']
                }, status=status.HTTP_200_OK)

            except OneTimePassword.DoesNotExist:
                return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    throttle_classes = [OTPThrottle]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            phone = serializer.data['phone_number']
            if generate_and_send_otp(phone):
                return Response({
                    "message": "Account created. OTP sent.",
                    "phone_number": phone
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": "Failed to send SMS."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    throttle_classes = [OTPThrottle]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.data['phone_number']
            if User.objects.filter(phone_number=phone).exists():
                if generate_and_send_otp(phone):
                    return Response({"message": "OTP sent for password reset."}, status=status.HTTP_200_OK)
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordConfirmView(APIView):
    throttle_classes = [OTPThrottle]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.data['phone_number']
            otp = serializer.data['otp']
            new_pass = serializer.data['new_password']
            try:
                otp_record = OneTimePassword.objects.get(phone_number=phone, otp=otp)
                user = User.objects.get(phone_number=phone)
                user.set_password(new_pass)
                user.save()
                otp_record.delete()
                return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
            except OneTimePassword.DoesNotExist:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)