from django.contrib import messages
from django.shortcuts import redirect, render
from django.conf import settings

from .google_sheets import GoogleSheetError, fetch_sheet_data


def sheet_value(row, field):
    wanted = field.casefold().replace(' ', '').replace('.', '')
    for key, value in row.items():
        normalized_key = key.casefold().replace(' ', '').replace('.', '')
        if normalized_key == wanted:
            return value.strip()
    return ''


def dashboard_context(user_type):
    try:
        sheet = fetch_sheet_data(
            settings.GOOGLE_SHEET_ID,
            settings.GOOGLE_SHEET_GID,
            settings.GOOGLE_SHEET_CSV_URL,
        )
        error = ''
    except GoogleSheetError as exc:
        sheet = {'headers': [], 'rows': [], 'table_rows': []}
        error = str(exc)

    visible_headers = [
        header for header in sheet['headers']
        if header.strip().casefold().replace(' ', '') != 'password'
    ]
    visible_indexes = [sheet['headers'].index(header) for header in visible_headers]
    visible_table_rows = [
        [row[index] for index in visible_indexes]
        for row in sheet['table_rows']
    ]
    return {
        'user_type': user_type,
        'sheet_headers': visible_headers,
        'sheet_rows': sheet['rows'],
        'sheet_table_rows': visible_table_rows,
        'sheet_count': len(sheet['rows']),
        'sheet_error': error,
    }


def worker_login(request):
    if request.session.get('worker_username'):
        return redirect('worker_dashboard')

    error = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        context = dashboard_context('worker')
        for worker in context['sheet_rows']:
            worker_username = sheet_value(worker, 'username')
            worker_password = sheet_value(worker, 'password')
            worker_status = sheet_value(worker, 'status')
            status_allowed = worker_status.casefold() not in {
                'inactive', 'disabled', 'blocked', 'deleted',
            }
            if (worker_username and worker_password
                    and worker_username.casefold() == username.casefold()
                    and worker_password == password
                    and status_allowed):
                request.session['worker_username'] = worker_username
                return redirect('worker_dashboard')
        error = 'Invalid username or password, or this account is inactive.'
        if context['sheet_error']:
            error = context['sheet_error']

    return render(request, 'worker_login.html', {'error': error})


def worker_logout(request):
    request.session.pop('worker_username', None)
    messages.info(request, 'You have been logged out.')
    return redirect('worker_login')


def employee_login(request):
    if request.session.get('employee_authenticated'):
        return redirect('employee_dashboard')

    error = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        if username == settings.EMPLOYEE_USERNAME and password == settings.EMPLOYEE_PASSWORD:
            request.session['employee_authenticated'] = True
            return redirect('employee_dashboard')
        error = 'Invalid employee username or password.'
    return render(request, 'employee_login.html', {'error': error})


def employee_logout(request):
    request.session.pop('employee_authenticated', None)
    messages.info(request, 'You have been logged out.')
    return redirect('employee_login')

# Home view
def home(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')


def appointment(request):
    return render(request, 'appointment.html')

# Worker Dashboard view
def worker_dashboard(request):
    username = request.session.get('worker_username')
    if not username:
        return redirect('worker_login')

    context = dashboard_context('worker')
    worker_rows = [
        row for row in context['sheet_rows']
        if sheet_value(row, 'username').casefold() == username.casefold()
    ]
    context['sheet_rows'] = worker_rows
    context['sheet_count'] = len(worker_rows)
    context['sheet_table_rows'] = [
        [row.get(header, '') for header in context['sheet_headers']]
        for row in worker_rows
    ]
    return render(request, 'worker_dashboard.html', context)

# Employer Dashboard view
def employer_dashboard(request):
    if not request.session.get('employee_authenticated'):
        return redirect('employee_login')
    return render(request, 'employer_dashboard.html', dashboard_context('employer'))


def employee_dashboard(request):
    if not request.session.get('employee_authenticated'):
        return redirect('employee_login')
    return render(request, 'employee_dashboard.html', dashboard_context('employee'))
