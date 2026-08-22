from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Yeh aapke homepage par views.home ko dikhayega
]