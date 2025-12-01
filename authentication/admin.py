from django.contrib import admin
from .models import User, OneTimePassword

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone_number', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('name', 'phone_number', 'id')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    ordering = ('-date_joined',)
    list_display_links = ('id', 'phone_number')

@admin.register(OneTimePassword)
class OneTimePasswordAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'otp', 'created_at')
    search_fields = ('phone_number',)
    ordering = ('-created_at',)