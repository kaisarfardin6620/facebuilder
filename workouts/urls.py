from django.urls import path
from .views import MyPlanView, CompleteSessionView, DashboardView

urlpatterns = [
    path('my-plan/', MyPlanView.as_view(), name='my-plan'),
    path('complete/', CompleteSessionView.as_view(), name='complete-session'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]