from django.urls import path
from .views import TestRevenueCatConnection

urlpatterns = [
    path('test-connection/', TestRevenueCatConnection.as_view(), name='test-rc'),
]