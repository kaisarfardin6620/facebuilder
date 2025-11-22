from django.urls import path
from .views import ScanFaceView

urlpatterns = [
    path('analyze/', ScanFaceView.as_view(), name='scan-face'),
]