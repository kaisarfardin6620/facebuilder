from django.urls import path
from .views import ChatCoachView

urlpatterns = [
    path('ask/', ChatCoachView.as_view(), name='ask-coach'),
]