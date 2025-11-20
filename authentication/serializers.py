import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import OneTimePassword

User = get_user_model()

def validate_phone_format(value):
    pattern = r'^\+?\d{10,15}$'
    if not re.match(pattern, value):
        raise serializers.ValidationError("Phone number must be in valid format, e.g. +12345678901")
    return value

def validate_complex_password(value):
    validate_password(value)
    
    if len(value) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.")
    
    if value.isdigit() or value.isalpha():
        raise serializers.ValidationError("Password must contain both letters and numbers.")
    
    return value

class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['phone_number', 'name', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_phone_number(self, value):
        return validate_phone_format(value)

    def validate_password(self, value):
        return validate_complex_password(value)

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.is_active = False 
        user.save()
        return user


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(validators=[validate_phone_format])
    otp = serializers.CharField(max_length=6)


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(validators=[validate_phone_format])
    password = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(validators=[validate_phone_format])


class ResetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(validators=[validate_phone_format])
    otp = serializers.CharField()
    new_password = serializers.CharField()

    def validate_new_password(self, value):
        return validate_complex_password(value)