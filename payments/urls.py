from django.urls import path
from .views import TestRevenueCatConnection, RevenueCatWebhookView

urlpatterns = [
    path('test-connection/', TestRevenueCatConnection.as_view(), name='test-rc'),
    path('webhook/', RevenueCatWebhookView.as_view(), name='revenuecat-webhook'),
]