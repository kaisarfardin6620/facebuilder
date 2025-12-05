from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from .models import User
from .utils import send_otp_via_twilio, verify_otp_via_twilio
from rest_framework.throttling import AnonRateThrottle

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

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
            return Response({"error": "Number incorrect"}, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return Response({"error": "Wrong password"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            send_otp_via_twilio(phone)
            return Response({"error": "Account not active. OTP sent to phone."}, status=status.HTTP_403_FORBIDDEN)

        tokens = get_tokens_for_user(user)

        return Response({
            "message": "Successfully Logged in.",
            "token": tokens['access'],
            "refresh_token": tokens['refresh'],
            "user_id": user.id
        }, status=status.HTTP_200_OK)

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
            except Exception:
                return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    throttle_classes = [OTPThrottle]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.data['phone_number']
            otp_input = serializer.data['otp']
            
            is_valid = verify_otp_via_twilio(phone, otp_input)

            if is_valid:
                try:
                    user = User.objects.get(phone_number=phone)
                    user.is_active = True
                    user.save()

                    tokens = get_tokens_for_user(user)

                    return Response({
                        "message": "Verification Successful",
                        "token": tokens['access'],
                        "refresh_token": tokens['refresh'],
                        "user_id": user.id
                    }, status=status.HTTP_200_OK)
                except User.DoesNotExist:
                    return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    throttle_classes = [OTPThrottle]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            phone = serializer.data['phone_number']
            
            if send_otp_via_twilio(phone):
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
                if send_otp_via_twilio(phone):
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

            if verify_otp_via_twilio(phone, otp):
                try:
                    user = User.objects.get(phone_number=phone)
                    user.set_password(new_pass)
                    user.save()
                    return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
                except User.DoesNotExist:
                    return Response({"error": "User error"}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendOTPView(APIView):
    throttle_classes = [OTPThrottle]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.data['phone_number']
            
            if not User.objects.filter(phone_number=phone).exists():
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

            if send_otp_via_twilio(phone):
                return Response({"message": "OTP has been resent successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Failed to send SMS."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)