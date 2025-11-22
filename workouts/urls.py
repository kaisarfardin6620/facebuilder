from django.urls import path
from .views import MyPlanView

urlpatterns = [
    path('my-plan/', MyPlanView.as_view(), name='my-plan'),
]