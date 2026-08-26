from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('service/', views.service, name='service'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('booking/', views.booking_view, name='booking'),
    
    # Universal Login & Routing
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('dashboard/', views.dashboard_redirect_view, name='dashboard_redirect'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),
    path('change-password/', views.admin_change_password_view, name='admin_change_password'),
    path('dashboard/action/', views.dashboard_action_view, name='dashboard_action'),
    path('dashboard/print/', views.print_dashboard_view, name='dashboard_print'),

    # Role Dashboards
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('staff-dashboard/', views.staff_dashboard_view, name='staff_dashboard'),
    path('doctor-dashboard/', views.doctor_dashboard_view, name='doctor_dashboard'),
    path('manager-dashboard/', views.manager_dashboard_view, name='manager_dashboard'),
    path('user-dashboard/', views.user_dashboard_view, name='user_dashboard'),
]