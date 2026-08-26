from django.shortcuts import render, redirect
from django.contrib import messages
from .google_sheets import (
    save_client_booking,
    authenticate_user,
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


# =========================================================================
# UNIVERSAL MULTI-ROLE AUTHENTICATION & ROUTING
# =========================================================================

def get_role_redirect(role_name):
    """Role अनुसार सहि Dashboard URL Path छान्ने Helper"""
    role = str(role_name).strip().lower()
    if 'admin' in role or 'owner' in role or 'super' in role:
        return 'admin_dashboard'
    elif 'doctor' in role or 'medical' in role:
        return 'doctor_dashboard'
    elif 'manager' in role:
        return 'manager_dashboard'
    elif 'staff' in role or 'reception' in role or 'employee' in role:
        return 'staff_dashboard'
    return 'user_dashboard'


def admin_login_view(request):
    """Google Sheet बाट सबै Role का Users Login गर्ने"""
    if request.session.get('admin_user'):
        role = request.session['admin_user'].get('role', 'User')
        return redirect(get_role_redirect(role))

    if request.method == 'POST':
        login_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate_user(login_input, password)
        if user:
            role = user.get('Role', 'Staff')
            request.session['admin_user'] = {
                'username': user.get('Username'),
                'email': user.get('Email', ''),
                'role': role,
                'profile_image': user.get('Profile_Image') or 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'
            }
            messages.success(request, f"Welcome {user.get('Username')} ({role})!")
            return redirect(get_role_redirect(role))
        else:
            messages.error(request, 'गलत Username / Email वा Password!')

    return render(request, 'admin_login.html')


def dashboard_redirect_view(request):
    """Navbar मा Dashboard क्लिक गर्दा आफ्नै Role को Dashboard मा लैजाने"""
    user = request.session.get('admin_user')
    if not user:
        return redirect('admin_login')
    return redirect(get_role_redirect(user.get('role', 'User')))


# =========================================================================
# 1. ADMIN DASHBOARD
# =========================================================================
def admin_dashboard_view(request):
    admin = request.session.get('admin_user')
    if not admin:
        return redirect('admin_login')
    bookings = get_all_client_bookings()
    if isinstance(bookings, list) and len(bookings) > 0:
        bookings = list(reversed(bookings))
    return render(request, 'admin_dashboard.html', {'admin': admin, 'bookings': bookings})


# =========================================================================
# 2. STAFF DASHBOARD
# =========================================================================
def staff_dashboard_view(request):
    staff = request.session.get('admin_user')
    if not staff:
        return redirect('admin_login')
    bookings = get_all_client_bookings()
    if isinstance(bookings, list) and len(bookings) > 0:
        bookings = list(reversed(bookings))
    return render(request, 'staff_dashboard.html', {'staff': staff, 'bookings': bookings})


# =========================================================================
# 3. DOCTOR DASHBOARD
# =========================================================================
def doctor_dashboard_view(request):
    doctor = request.session.get('admin_user')
    if not doctor:
        return redirect('admin_login')
    bookings = get_all_client_bookings()
    if isinstance(bookings, list) and len(bookings) > 0:
        bookings = list(reversed(bookings))
    return render(request, 'doctor_dashboard.html', {'doctor': doctor, 'bookings': bookings})


# =========================================================================
# 4. MANAGER DASHBOARD
# =========================================================================
def manager_dashboard_view(request):
    manager = request.session.get('admin_user')
    if not manager:
        return redirect('admin_login')
    bookings = get_all_client_bookings()
    if isinstance(bookings, list) and len(bookings) > 0:
        bookings = list(reversed(bookings))
    return render(request, 'manager_dashboard.html', {'manager': manager, 'bookings': bookings})


# =========================================================================
# 5. GENERAL USER DASHBOARD
# =========================================================================
def user_dashboard_view(request):
    user = request.session.get('admin_user')
    if not user:
        return redirect('admin_login')
    return render(request, 'user_dashboard.html', {'user': user})


# Password Change & Logout
def admin_change_password_view(request):
    user = request.session.get('admin_user')
    if not user:
        return redirect('admin_login')

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if new_password != confirm_password:
            messages.error(request, 'नयाँ पासवर्ड मिलेन!')
            return redirect(get_role_redirect(user.get('role')))

        if update_admin_password_sheet(user['username'], new_password):
            messages.success(request, 'Google Sheet मा पासवर्ड सफलतापूर्वक परिवर्तन भयो!')
        else:
            messages.error(request, 'पासवर्ड परिवर्तन हुन सकेन।')

    return redirect(get_role_redirect(user.get('role')))


def admin_logout_view(request):
    if 'admin_user' in request.session:
        del request.session['admin_user']
    messages.success(request, 'सफलतापूर्वक लगआउट हुनुभयो।')
    return redirect('admin_login')