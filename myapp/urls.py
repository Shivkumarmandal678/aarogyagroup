from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('chairman/', views.chairman, name='chairman'),
    path('service/', views.service, name='service'),
    path('chatbot/', views.chatbot, name='chatbot'),
]
