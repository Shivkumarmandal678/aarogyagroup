from django.shortcuts import render, redirect
from django.contrib import messages
from .google_sheets import save_client_booking, get_admin_by_username

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def chairman(request):
    return render(request, 'chairman.html')

def service(request):
    return render(request, 'services.html')

def chatbot(request):
    return render(request, 'chatbot.html')

# Booking View -> Data सिधै Google Sheet मा जान्छ
def booking_view(request):
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'phone': request.POST.get('phone'),
            'email': request.POST.get('email'),
            'department': request.POST.get('department'),
            'date': request.POST.get('date'),
            'message': request.POST.get('message'),
        }
        
        # Google Sheet मा सेभ गर्ने
        success = save_client_booking(data)
        
        if success:
            messages.success(request, 'धन्यवाद! तपाईँको Booking सफलतापूर्वक Google Sheet मा सुरक्षित भयो।')
        else:
            messages.info(request, 'Booking प्राप्त भयो। हामी छिट्टै सम्पर्क गर्नेछौं।')
            
        return redirect('booking')
        
    return render(request, 'booking.html')