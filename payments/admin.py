from django.contrib import admin
from .models import Subscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'plan_name', 'expiry_date', 'last_checked')
    list_filter = ('is_active', 'plan_name', 'last_checked')
    search_fields = ('user__name', 'user__phone_number', 'plan_name')
    readonly_fields = ('last_checked',)
    ordering = ('-last_checked',)