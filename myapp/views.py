from django.shortcuts import render, redirect
from django.contrib import messages
from .google_sheets import (
    save_client_booking,
    get_admin_by_username,
    update_admin_password_sheet,
    get_all_client_bookings
)

# Public Views
def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def service(request):
    return render(request, 'services.html')

def chatbot(request):
    return render(request, 'chatbot.html')

# Booking View
def booking_view(request):
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'service': request.POST.get('service', '').strip(),
            'date': request.POST.get('date', '').strip(),
            'message': request.POST.get('message', '').strip(),
        }
        
        if save_client_booking(data):
            messages.success(request, 'धन्यवाद! तपाईँको Booking सफलतापूर्वक सुरक्षित भयो।')
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
    """Admin Dashboard"""
    admin = request.session.get('admin_user')
    if not admin:
        messages.warning(request, 'कृपया पहिले लगइन गर्नुहोस्!')
        return redirect('admin_login')

    bookings = get_all_client_bookings()
    if isinstance(bookings, list):
        bookings = list(reversed(bookings))

    return render(request, 'admin_dashboard.html', {
        'admin': admin,
        'bookings': bookings
    })

def admin_change_password_view(request):
    """Google Sheet मा Password Update गर्ने"""
    admin = request.session.get('admin_user')
    if not admin:
        return redirect('admin_login')

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if new_password != confirm_password:
            messages.error(request, 'नयाँ पासवर्ड मिलेन!')
            return redirect('admin_dashboard')

        if update_admin_password_sheet(admin['username'], new_password):
            messages.success(request, 'Google Sheet मा पासवर्ड सफलतापूर्वक परिवर्तन भयो!')
        else:
            messages.error(request, 'पासवर्ड परिवर्तन हुन सकेन।')

    return redirect('admin_dashboard')

def admin_logout_view(request):
    """Admin Logout"""
    if 'admin_user' in request.session:
        del request.session['admin_user']
    messages.success(request, 'सफलतापूर्वक लगआउट हुनुभयो।')
    return redirect('admin_login')