from django.shortcuts import render, redirect
from django.contrib import messages
from .google_sheets import (
    save_client_booking,
    get_all_clients,
    get_admin_by_username,
    update_admin_password_sheet
)

# Public Pages
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

# Booking Page
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
        
        success = save_client_booking(data)
        if success:
            messages.success(request, 'धन्यवाद! तपाईँको Booking Google Sheet मा सुरक्षित भयो।')
        else:
            messages.info(request, 'Booking प्राप्त भयो। हामी छिट्टै सम्पर्क गर्नेछौं।')
        return redirect('booking')
        
    return render(request, 'booking.html')

# ==========================================
# ADMIN AUTHENTICATION & DASHBOARD
# ==========================================

def admin_login_view(request):
    """Google Sheet बाट Admin Login गर्ने"""
    if request.session.get('admin_user'):
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        admin = get_admin_by_username(username)
        
        # Google Sheet को Password सँग मिलाउने
        if admin and str(admin.get('Password', '')).strip() == password:
            request.session['admin_user'] = {
                'username': admin.get('Username'),
                'email': admin.get('Email', ''),
                'role': admin.get('Role', 'Administrator'),
                'profile_image': admin.get('Profile_Image') or 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'
            }
            messages.success(request, f"Welcome {admin.get('Username')}!")
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'गलत Username वा Password!')

    return render(request, 'admin_login.html')

def admin_dashboard_view(request):
    """Admin Dashboard - Profile र Client Bookings देखाउने"""
    admin = request.session.get('admin_user')
    if not admin:
        messages.warning(request, 'कृपया पहिले लगइन गर्नुहोस्!')
        return redirect('admin_login')

    bookings = get_all_clients()
    return render(request, 'admin_dashboard.html', {'admin': admin, 'bookings': bookings})

def admin_change_password_view(request):
    """Google Sheet मा Password फेर्ने"""
    admin = request.session.get('admin_user')
    if not admin:
        return redirect('admin_login')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, 'दुवै पासवर्ड मिलेनन्!')
            return redirect('admin_dashboard')

        success = update_admin_password_sheet(admin['username'], new_password)
        if success:
            messages.success(request, 'Google Sheet मा पासवर्ड सफलतापूर्वक अपडेट भयो!')
        else:
            messages.error(request, 'पासवर्ड अपडेट गर्न सकिएन।')

    return redirect('admin_dashboard')

def admin_logout_view(request):
    """Admin Session हटाएर Logout गर्ने"""
    if 'admin_user' in request.session:
        del request.session['admin_user']
    messages.success(request, 'सफलतापूर्वक लगआउट हुनुभयो।')
    return redirect('admin_login')