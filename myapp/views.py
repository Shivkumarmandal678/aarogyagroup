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

    return {
        'user_type': user_type,
        'sheet_headers': sheet['headers'],
        'sheet_rows': sheet['rows'],
        'sheet_table_rows': sheet['table_rows'],
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
            status_allowed = not worker_status or worker_status.casefold() == 'active'
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

# Home view
def home(request):
    return render(request, 'home.html')

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
    context['sheet_headers'] = [
        header for header in context['sheet_headers']
        if header.strip().casefold().replace(' ', '') != 'password'
    ]
    context['sheet_table_rows'] = [
        [row.get(header, '') for header in context['sheet_headers']]
        for row in worker_rows
    ]
    return render(request, 'worker_dashboard.html', context)

# Employer Dashboard view
def employer_dashboard(request):
    return render(request, 'employer_dashboard.html', dashboard_context('employer'))
