from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('appointment/', views.appointment, name='appointment'),
    path('worker/login/', views.worker_login, name='worker_login'),
    path('worker/logout/', views.worker_logout, name='worker_logout'),
    path('worker/dashboard/', views.worker_dashboard, name='worker_dashboard'),
    path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),
    path('employee/login/', views.employee_login, name='employee_login'),
    path('employee/logout/', views.employee_logout, name='employee_logout'),
    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),
]
