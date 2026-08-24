import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from .google_sheets import register_user_to_sheet, get_user_by_username, update_user_password

# Home / Dashboard View (नयाँ थपिएको)
def home(request):
    username = request.session.get('user')
    # यदि login भएको छैन भने सिधै login पेजमा पठाउने वा home देखाउने
    if not username:
        return redirect('login')
    return render(request, 'home.html', {'username': username})

# Registration View
def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        phone = request.POST['phone']
        address = request.POST['address']
        password = request.POST['password']
        
        otp = str(random.randint(100000, 999999))
        request.session['temp_user'] = {
            'username': username, 'email': email, 'phone': phone,
            'address': address, 'password': password, 'otp': otp
        }
        
        # Send OTP Email
        send_mail(
            'Aarogya Group - OTP Verification',
            f'Aapka OTP code: {otp}',
            None,
            [email],
            fail_silently=False,
        )
        messages.success(request, 'OTP aapke email par bhej diya gaya hai.')
        return redirect('verify_otp')
        
    return render(request, 'register.html')

# OTP Verification View
def verify_otp_view(request):
    temp_user = request.session.get('temp_user')
    if not temp_user:
        return redirect('register')

    if request.method == 'POST':
        user_otp = request.POST['otp']
        if user_otp == temp_user['otp']:
            register_user_to_sheet(temp_user)
            del request.session['temp_user']
            messages.success(request, 'Account Verify ho gaya! Google Sheet me save kar diya gaya hai.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid OTP! Fir se try karein.')

    return render(request, 'verify_otp.html')

# Login View (Fetches data from Google Sheet)
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = get_user_by_username(username)
        if user and str(user.get('Password')) == password:
            request.session['user'] = user['Username']
            messages.success(request, f"Welcome {user['Username']}!")
            return redirect('home')
        else:
            messages.error(request, 'Invalid Username ya Password!')
            
    return render(request, 'login.html')

# Forgot Password View
def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        otp = str(random.randint(100000, 999999))
        request.session['reset_email'] = email
        request.session['reset_otp'] = otp
        
        send_mail(
            'Aarogya Group - Reset Password OTP',
            f'Password Reset karne ke liye OTP: {otp}',
            None,
            [email],
            fail_silently=False,
        )
        messages.success(request, 'Reset OTP email par bhej diya gaya hai.')
        return redirect('reset_password')
        
    return render(request, 'forgot_password.html')

# Reset Password View
def reset_password_view(request):
    if request.method == 'POST':
        user_otp = request.POST['otp']
        new_password = request.POST['new_password']
        
        if user_otp == request.session.get('reset_otp'):
            email = request.session.get('reset_email')
            if update_user_password(email, new_password):
                messages.success(request, 'Password successfully update ho gaya!')
                return redirect('login')
        messages.error(request, 'Invalid OTP ya error aayi!')

    return render(request, 'reset_password.html')

# Logout View (नयाँ थपिएको)
def logout_view(request):
    request.session.flush()
    messages.success(request, 'Logged out successfully!')
    return redirect('login')



# About View
def about_view(request):
    return render(request, 'about.html')

# Booking View (अहिलेको लागि home वा booking.html)
def booking_view(request):
    return render(request, 'booking.html') # वा 'booking.html' यदि छ भने

def services_view(request):
    return render(request, 'services.html')
