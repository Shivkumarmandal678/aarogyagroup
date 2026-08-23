from django.shortcuts import render
from django.http import HttpResponse

# Home view
def home(request):
    return render(request, 'home.html')

# Worker Dashboard view
def worker_dashboard(request):
    context = {
        'user_type': 'worker'
    }
    return render(request, 'worker_dashboard.html', context)

# Employer Dashboard view
def employer_dashboard(request):
    context = {
        'user_type': 'employer'
    }
    return render(request, 'employer_dashboard.html', context)
