from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('chairman/', views.chairman, name='chairman'),
    path('service/', views.service, name='service'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('booking/', views.booking_view, name='booking'),
    
    # Admin URLs
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-change-password/', views.admin_change_password_view, name='admin_change_password'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),
]