from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4
from django.utils import timezone
from django.contrib import messages
from .google_sheets import (
    save_client_booking,
    authenticate_user,
    update_admin_password_sheet,
    get_all_client_bookings,
    get_all_reports,
    post_sheet_action,
    SHEET_ID,
    looks_like_demo_submission,
)

def render_public_page(request, template_name, context=None):
    response = render(request, template_name, context or {})
    response["Cache-Control"] = "public, max-age=300, s-maxage=600"
    response["Vary"] = "Accept-Encoding"
    response["X-Content-Type-Options"] = "nosniff"
    return response


# Public Views
def home(request):
    return render_public_page(request, 'home.html')


def sitemap_view(request):
    base_url = request.build_absolute_uri('/').rstrip('/')
    pages = [
        ('', 'daily', '1.0'),
        ('about/', 'daily', '0.9'),
        ('service/', 'daily', '0.9'),
        ('booking/', 'daily', '0.8'),
    ]
    url_items = []
    today = date.today().isoformat()
    for path, changefreq, priority in pages:
        url_items.append(
            f"""  <url>
    <loc>{base_url}/{path}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""
        )
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(url_items)}
</urlset>
'''
    response = HttpResponse(xml, content_type='application/xml')
    response["Cache-Control"] = "public, max-age=1800, s-maxage=3600"
    response["Vary"] = "Accept-Encoding"
    return response


def about(request):
    return render_public_page(request, 'about.html')


def service(request):
    return render_public_page(request, 'services.html')


def chatbot(request):
    return render_public_page(request, 'chatbot.html')

CLASS_WEEKDAYS = {1, 3, 6}
CLASS_CUTOFF_HOUR = 10
BOOKING_COUNTRIES = (
    'United Arab Emirates (UAE)',
    'Saudi Arabia',
    'Qatar',
    'Kuwait',
    'Bahrain',
    'Oman',
    'Malaysia',
)
PASSPORT_UPLOAD_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf'}
PASSPORT_UPLOAD_CONTENT_TYPES = {'image/jpeg', 'image/png', 'application/pdf'}
PASSPORT_UPLOAD_MAX_BYTES = 5 * 1024 * 1024


def _save_passport_copy(uploaded_file):
    if not uploaded_file:
        return None, None
    extension = Path(uploaded_file.name or '').suffix.lower()
    if extension not in PASSPORT_UPLOAD_EXTENSIONS or uploaded_file.content_type not in PASSPORT_UPLOAD_CONTENT_TYPES:
        return None, 'Passport copy must be a JPG, PNG, or PDF file.'
    if uploaded_file.size > PASSPORT_UPLOAD_MAX_BYTES:
        return None, 'Passport copy must be 5 MB or smaller.'
    storage_path = default_storage.save(f'passport_uploads/{uuid4().hex}{extension}', uploaded_file)
    return storage_path, None


def next_class_date(current=None):
    current = current or timezone.localtime()
    class_date = current.date()
    if class_date.weekday() in CLASS_WEEKDAYS and current.hour < CLASS_CUTOFF_HOUR:
        return class_date
    while True:
        class_date += timedelta(days=1)
        if class_date.weekday() in CLASS_WEEKDAYS:
            return class_date


def is_valid_class_date(value, current=None):
    try:
        selected = date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return False
    return selected == next_class_date(current)


# Booking View
def booking_view(request):
    if request.method == 'POST':
        selected_date = request.POST.get('date', '').strip()
        if not is_valid_class_date(selected_date):
            messages.error(request, 'Please select the next available class date: Sunday, Tuesday, or Thursday.')
            response = render(request, 'booking.html', {'next_class_date': next_class_date().isoformat(), 'countries': BOOKING_COUNTRIES})
            response["Cache-Control"] = "public, max-age=300, s-maxage=600"
            return response
        data = {
            'name': request.POST.get('name', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'passport_number': request.POST.get('passport_number', '').strip(),
            'address': request.POST.get('address', '').strip(),
            'lot_number': request.POST.get('lot_number', '').strip(),
            'service': request.POST.get('service', '').strip(),
            'country': request.POST.get('country', '').strip(),
            'date': request.POST.get('date', '').strip(),
            'message': request.POST.get('message', '').strip(),
        }
        required_fields = ['name', 'phone', 'email', 'passport_number', 'address', 'service', 'country', 'date', 'message']
        if any(not data.get(field, '').strip() for field in required_fields):
            messages.error(request, 'Please fill in all required fields. Lot number is optional; passport copy is required.')
            response = render(request, 'booking.html', {'next_class_date': next_class_date().isoformat(), 'countries': BOOKING_COUNTRIES, **data})
            response["Cache-Control"] = "public, max-age=300, s-maxage=600"
            return response
        if data['country'] not in BOOKING_COUNTRIES:
            messages.error(request, 'Please select a valid destination country.')
            response = render(request, 'booking.html', {'next_class_date': next_class_date().isoformat(), 'countries': BOOKING_COUNTRIES, **data})
            response["Cache-Control"] = "public, max-age=300, s-maxage=600"
            return response
        if looks_like_demo_submission(data):
            messages.error(request, 'Demo or fake booking entries are blocked. Please enter your real details only.')
            response = render(request, 'booking.html', {'next_class_date': next_class_date().isoformat(), 'countries': BOOKING_COUNTRIES})
            response["Cache-Control"] = "public, max-age=300, s-maxage=600"
            return response
        if not request.FILES.get('passport_copy'):
            messages.error(request, 'Please upload a passport copy. JPG, PNG or PDF files up to 5 MB are accepted.')
            response = render(request, 'booking.html', {'next_class_date': next_class_date().isoformat(), 'countries': BOOKING_COUNTRIES, **data})
            response["Cache-Control"] = "public, max-age=300, s-maxage=600"
            return response
        passport_copy_path, upload_error = _save_passport_copy(request.FILES.get('passport_copy'))
        if upload_error:
            messages.error(request, upload_error)
            response = render(request, 'booking.html', {'next_class_date': next_class_date().isoformat(), 'countries': BOOKING_COUNTRIES, **data})
            response["Cache-Control"] = "public, max-age=300, s-maxage=600"
            return response
        data['passport_copy'] = passport_copy_path or ''
        if save_client_booking(data):
            messages.success(request, 'Thank you! Your booking was saved successfully.')
        else:
            if passport_copy_path:
                default_storage.delete(passport_copy_path)
            messages.info(request, 'Booking received. Our team will contact you soon.')
        return redirect('booking')
    response = render(request, 'booking.html', {'next_class_date': next_class_date().isoformat(), 'countries': BOOKING_COUNTRIES})
    response["Cache-Control"] = "public, max-age=300, s-maxage=600"
    response["Vary"] = "Accept-Encoding"
    return response


# =========================================================================
# UNIVERSAL MULTI-ROLE AUTHENTICATION & ROUTING
# =========================================================================

def get_role_redirect(role_name):
    """Return the correct dashboard route for a given role."""
    role = ''.join(char for char in str(role_name).strip().lower() if char.isalnum())
    if role in {'admin', 'administrator', 'owner', 'superadmin'}:
        return 'admin_dashboard'
    elif 'doctor' in role or 'medical' in role:
        return 'doctor_dashboard'
    elif 'manager' in role:
        return 'manager_dashboard'
    elif 'staff' in role or 'reception' in role or 'employee' in role:
        return 'staff_dashboard'
    return 'user_dashboard'


def _logged_in_user(request):
    return request.session.get('admin_user')


def _is_admin(user):
    role = ''.join(char for char in str(user.get('role', '')).strip().lower() if char.isalnum())
    return role in {'admin', 'administrator', 'owner', 'superadmin'}


def _require_dashboard_role(request, role):
    """Allow admins everywhere, but keep each other role on its own portal."""
    user = _logged_in_user(request)
    if not user:
        return None, redirect('admin_login')
    if not _is_admin(user) and get_role_redirect(user.get('role')) != role:
        return user, redirect(get_role_redirect(user.get('role')))
    return user, None


def _dashboard_context(dashboard_user, **extra):
    return {
        'sheet_url': f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit',
        **extra,
    }


def _row_value(row, *keys):
    for key in keys:
        if row.get(key):
            return str(row[key]).strip()
    return ''


def _normalize_report(row):
    normalized = dict(row)
    fields = ('id', 'patient_name', 'patient_email', 'test_name', 'result', 'doctor', 'doctor_status', 'manager_status', 'staff_status', 'user_status')
    for field in fields:
        normalized[field] = _row_value(row, field, field.title().replace('_', ' '), field.title(), field.upper())
    return normalized


def _dashboard_records(user):
    bookings = get_all_client_bookings()
    reports = [_normalize_report(row) for row in get_all_reports()]
    role = get_role_redirect(user.get('role'))
    if role == 'user_dashboard':
        identity = {user.get('username', '').lower(), user.get('email', '').lower()}
        bookings = [row for row in bookings if _row_value(row, 'Email', 'User_Email').lower() in identity]
        reports = [row for row in reports if _row_value(row, 'Patient_Email', 'Email').lower() in identity and _row_value(row, 'Staff_Status', 'Status').lower() in {'approved', 'staff approved', 'complete', 'completed'}]
    elif role == 'doctor_dashboard':
        reports = [row for row in reports if not _row_value(row, 'Doctor', 'Doctor_Username') or _row_value(row, 'Doctor', 'Doctor_Username').lower() == user.get('username', '').lower()]
    elif role == 'manager_dashboard':
        reports = [row for row in reports if _row_value(row, 'Doctor_Status', 'Status').lower() in {'pending', 'submitted', 'doctor approved', 'approved'}]
    elif role == 'staff_dashboard':
        reports = [row for row in reports if _row_value(row, 'Manager_Status').lower() in {'approved', 'manager approved'}]
    return list(reversed(bookings or [])), list(reversed(reports or []))


def admin_login_view(request):
    """Log in users from the Google Sheet by role."""
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
            messages.error(request, 'Invalid username or password.')

    return render(request, 'admin_login.html')


def dashboard_redirect_view(request):
    """Send the user to their correct dashboard from the navbar."""
    user = request.session.get('admin_user')
    if not user:
        return redirect('admin_login')
    return redirect(get_role_redirect(user.get('role', 'User')))


# =========================================================================
# 1. ADMIN DASHBOARD
# =========================================================================
def admin_dashboard_view(request):
    admin, response = _require_dashboard_role(request, 'admin_dashboard')
    if response:
        return response
    bookings, reports = _dashboard_records(admin)
    return render(request, 'admin_dashboard.html', _dashboard_context(admin, admin=admin, bookings=bookings, reports=reports, can_manage=True))


# =========================================================================
# 2. STAFF DASHBOARD
# =========================================================================
def staff_dashboard_view(request):
    staff, response = _require_dashboard_role(request, 'staff_dashboard')
    if response:
        return response
    bookings, reports = _dashboard_records(staff)
    return render(request, 'staff_dashboard.html', _dashboard_context(staff, staff=staff, bookings=bookings, reports=reports, can_approve=True))


# =========================================================================
# 3. DOCTOR DASHBOARD
# =========================================================================
def doctor_dashboard_view(request):
    doctor, response = _require_dashboard_role(request, 'doctor_dashboard')
    if response:
        return response
    bookings, reports = _dashboard_records(doctor)
    return render(request, 'doctor_dashboard.html', _dashboard_context(doctor, doctor=doctor, bookings=bookings, reports=reports, can_create=True))


# =========================================================================
# 4. MANAGER DASHBOARD
# =========================================================================
def manager_dashboard_view(request):
    manager, response = _require_dashboard_role(request, 'manager_dashboard')
    if response:
        return response
    bookings, reports = _dashboard_records(manager)
    return render(request, 'manager_dashboard.html', _dashboard_context(manager, manager=manager, bookings=bookings, reports=reports, can_approve=True))


# =========================================================================
# 5. GENERAL USER DASHBOARD
# =========================================================================
def user_dashboard_view(request):
    user, response = _require_dashboard_role(request, 'user_dashboard')
    if response:
        return response
    bookings, reports = _dashboard_records(user)
    return render(request, 'user_dashboard.html', _dashboard_context(user, user=user, bookings=bookings, reports=reports))


@require_POST
def dashboard_action_view(request):
    user = _logged_in_user(request)
    if not user:
        return redirect('admin_login')
    role = get_role_redirect(user.get('role'))
    action = request.POST.get('action', '').strip()
    allowed = {
        'admin_dashboard': {'booking_create', 'booking_update', 'booking_delete', 'report_create', 'report_update', 'report_delete'},
        'doctor_dashboard': {'report_create', 'report_update'},
        'manager_dashboard': {'report_manager_approve', 'report_manager_reject'},
        'staff_dashboard': {'report_staff_approve', 'report_staff_reject'},
        'user_dashboard': {'booking_create'},
    }
    if not _is_admin(user) and action not in allowed.get(role, set()):
        messages.error(request, 'This action is not allowed for your role.')
        return redirect(get_role_redirect(user.get('role')))

    data = {key: value.strip() for key, value in request.POST.items() if key not in {'csrfmiddlewaretoken', 'action'}}
    data['updated_by'] = user.get('username', '')
    data['updated_at'] = datetime.now().strftime('%Y-%m-%d %I:%M %p')
    if action == 'report_create':
        data.update({'doctor': user.get('username', ''), 'doctor_status': 'Pending Manager Approval', 'manager_status': 'Pending', 'staff_status': 'Pending', 'user_status': 'Hidden'})
    elif action == 'report_manager_approve':
        data.update({'manager_status': 'Approved', 'staff_status': 'Pending Staff Approval'})
    elif action == 'report_manager_reject':
        data.update({'manager_status': 'Rejected', 'staff_status': 'Hidden', 'user_status': 'Hidden'})
    elif action == 'report_staff_approve':
        data.update({'staff_status': 'Approved', 'user_status': 'Visible'})
    elif action == 'report_staff_reject':
        data.update({'staff_status': 'Rejected', 'user_status': 'Hidden'})

    sheet_action = {
        'booking_create': 'add_booking', 'booking_update': 'update_booking', 'booking_delete': 'delete_booking',
        'report_create': 'add_report', 'report_update': 'update_report', 'report_delete': 'delete_report',
        'report_manager_approve': 'update_report', 'report_manager_reject': 'update_report',
        'report_staff_approve': 'update_report', 'report_staff_reject': 'update_report',
    }.get(action)
    if sheet_action and post_sheet_action(sheet_action, data):
        messages.success(request, 'Update saved successfully.')
    else:
        messages.error(request, 'Update could not be saved in Google Sheet.')
    return redirect(get_role_redirect(user.get('role')))


def print_dashboard_view(request):
    user = _logged_in_user(request)
    if not user:
        return redirect('admin_login')
    return render(request, 'dashboard_print.html', {'user': user, 'bookings': _dashboard_records(user)[0], 'reports': _dashboard_records(user)[1]})


# Password Change & Logout
def admin_change_password_view(request):
    user = request.session.get('admin_user')
    if not user:
        return redirect('admin_login')

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect(get_role_redirect(user.get('role')))

        if update_admin_password_sheet(user['username'], new_password):
            messages.success(request, 'Password changed successfully in Google Sheets.')
        else:
            messages.error(request, 'Password could not be changed.')

    return redirect(get_role_redirect(user.get('role')))


def admin_logout_view(request):
    if 'admin_user' in request.session:
        del request.session['admin_user']
    messages.success(request, 'You have logged out successfully.')
    return redirect('admin_login')