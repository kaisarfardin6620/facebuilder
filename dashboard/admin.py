from django.contrib import admin
from .models import SubscriptionPlan, Subscription, PaymentHistory

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

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_name', 'amount', 'transaction_date', 'transaction_id')
    list_filter = ('transaction_date', 'plan_name')
    search_fields = ('user__phone_number', 'user__name', 'transaction_id')
    readonly_fields = ('transaction_date',)
    ordering = ('-transaction_date',)