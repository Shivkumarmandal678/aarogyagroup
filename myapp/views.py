from django.contrib import messages
from django.shortcuts import redirect, render
from django.conf import settings


# Home view
def home(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')

