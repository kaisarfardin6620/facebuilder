from django.urls import path
from .views import ScanFaceView, SetGoalsView

urlpatterns = [
    path('analyze/', ScanFaceView.as_view(), name='scan-face'),
    path('set-goals/', SetGoalsView.as_view(), name='set-goals'),
]