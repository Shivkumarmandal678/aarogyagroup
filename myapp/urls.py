from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('worker/dashboard/', views.worker_dashboard, name='worker_dashboard'),
    path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),
]
