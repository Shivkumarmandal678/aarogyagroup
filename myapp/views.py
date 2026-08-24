from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def services(request):
    return render(request, 'services.html')

def booking(request):
    return render(request, 'booking.html')

def login_view(request):
    return render(request, 'login.html')