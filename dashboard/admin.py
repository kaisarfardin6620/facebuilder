from django.contrib import admin
from .models import SubscriptionPlan, Subscription

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration', 'market_product_id', 'is_active', 'created_at')
    list_filter = ('is_active', 'duration')
    search_fields = ('name', 'market_product_id')
    ordering = ('-created_at',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'plan_name', 'expiry_date', 'last_checked')
    list_filter = ('is_active', 'last_checked')
    search_fields = ('user__phone_number', 'user__name')
    readonly_fields = ('last_checked',)