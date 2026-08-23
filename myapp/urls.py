from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('worker/login/', views.worker_login, name='worker_login'),
    path('worker/logout/', views.worker_logout, name='worker_logout'),
    path('worker/dashboard/', views.worker_dashboard, name='worker_dashboard'),
    path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),
]
