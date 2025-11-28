from adrf.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from .models import User
from .utils import send_otp_via_twilio, verify_otp_via_twilio
from rest_framework.throttling import AnonRateThrottle
from asgiref.sync import sync_to_async

@sync_to_async
def get_tokens_for_user_async(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

send_otp_async = sync_to_async(send_otp_via_twilio, thread_sensitive=False)
verify_otp_async = sync_to_async(verify_otp_via_twilio, thread_sensitive=False)

class OTPThrottle(AnonRateThrottle):
    scope = 'otp'

class LoginView(APIView):
    throttle_classes = [OTPThrottle]

    async def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.data['phone_number']
        password = serializer.data['password']

        try:
            user = await User.objects.aget(phone_number=phone)
        except User.DoesNotExist:
            return Response({"error": "Number incorrect"}, status=status.HTTP_404_NOT_FOUND)

        is_correct = await sync_to_async(user.check_password)(password)
        if not is_correct:
            return Response({"error": "Wrong password"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            await send_otp_async(phone)
            return Response({"error": "Account not active. OTP sent to phone."}, status=status.HTTP_403_FORBIDDEN)

        tokens = await get_tokens_for_user_async(user)

        return Response({
            "message": "Successfully Logged in.",
            "token": tokens['access'],
            "refresh_token": tokens['refresh']
        }, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    throttle_classes = [OTPThrottle]

    async def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.data['phone_number']
            otp_input = serializer.data['otp']
            
            is_valid = await verify_otp_async(phone, otp_input)

            if is_valid:
                try:
                    user = await User.objects.aget(phone_number=phone)
                    user.is_active = True
                    await user.asave()

                    tokens = await get_tokens_for_user_async(user)

                    return Response({
                        "message": "Verification Successful",
                        "token": tokens['access'],
                        "refresh_token": tokens['refresh']
                    }, status=status.HTTP_200_OK)
                except User.DoesNotExist:
                    return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    throttle_classes = [OTPThrottle]

    async def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            await sync_to_async(serializer.save)()
            
            phone = serializer.data['phone_number']
            
            if await send_otp_async(phone):
                return Response({
                    "message": "Account created. OTP sent.",
                    "phone_number": phone
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": "Failed to send SMS."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    throttle_classes = [OTPThrottle]

    async def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.data['phone_number']
            exists = await User.objects.filter(phone_number=phone).aexists()
            if exists:
                if await send_otp_async(phone):
                    return Response({"message": "OTP sent for password reset."}, status=status.HTTP_200_OK)
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordConfirmView(APIView):
    throttle_classes = [OTPThrottle]

    async def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.data['phone_number']
            otp = serializer.data['otp']
            new_pass = serializer.data['new_password']

            if await verify_otp_async(phone, otp):
                try:
                    user = await User.objects.aget(phone_number=phone)
                    user.set_password(new_pass)
                    await user.asave()
                    return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
                except User.DoesNotExist:
                    return Response({"error": "User error"}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)