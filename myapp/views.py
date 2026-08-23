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


def without_login_fields(headers, rows):
    visible_headers = [
        header for header in headers
        if header.strip().casefold().replace(' ', '') not in {'username', 'password'}
    ]
    return visible_headers, [
        [row.get(header, '') for header in visible_headers]
        for row in rows
    ]


def dashboard_context(user_type, csv_url=None):
    try:
        sheet = fetch_sheet_data(
            settings.GOOGLE_SHEET_ID,
            settings.GOOGLE_SHEET_GID,
            csv_url or settings.WORKER_SHEET_CSV_URL or settings.GOOGLE_SHEET_CSV_URL,
        )
        error = ''
    except GoogleSheetError as exc:
        sheet = {'headers': [], 'rows': [], 'table_rows': []}
        error = str(exc)

    visible_headers, visible_table_rows = without_login_fields(
        sheet['headers'], sheet['rows'],
    )
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
        context = dashboard_context('worker', settings.WORKER_SHEET_CSV_URL)
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
        context = dashboard_context('employee', settings.EMPLOYEE_SHEET_CSV_URL)
        for employee in context['sheet_rows']:
            employee_username = sheet_value(employee, 'username')
            employee_password = sheet_value(employee, 'password')
            employee_status = sheet_value(employee, 'status').casefold()
            status_allowed = employee_status not in {'inactive', 'disabled', 'blocked', 'deleted'}
            if (employee_username and employee_password
                    and employee_username.casefold() == username.casefold()
                    and employee_password == password and status_allowed):
                request.session['employee_authenticated'] = True
                return redirect('employee_dashboard')
        error = 'Invalid employee username or password.'
        if context['sheet_error']:
            error = context['sheet_error']
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

    context = dashboard_context('worker', settings.WORKER_SHEET_CSV_URL)
    context['sheet_rows'] = []
    context['sheet_table_rows'] = []
    context['sheet_count'] = 0
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
    try:
        client_sheet = fetch_sheet_data(
            settings.GOOGLE_SHEET_ID, '', settings.CLIENT_SHEET_CSV_URL,
        )
        context['client_headers'] = [
            header for header in client_sheet['headers']
            if header.strip().casefold().replace(' ', '') not in {'username', 'password'}
        ]
        context['client_rows'] = [
            [row[index] for index, header in enumerate(client_sheet['headers'])
             if header in context['client_headers']]
            for row in client_sheet['table_rows']
        ]
        context['client_error'] = ''
    except GoogleSheetError as exc:
        context['client_headers'] = []
        context['client_rows'] = []
        context['client_error'] = str(exc)
    return render(request, 'worker_dashboard.html', context)

# Employer Dashboard view
def employer_dashboard(request):
    if not request.session.get('employee_authenticated'):
        return redirect('employee_login')
    return render(request, 'employer_dashboard.html', dashboard_context('employer', settings.WORKER_SHEET_CSV_URL))


def employee_dashboard(request):
    if not request.session.get('employee_authenticated'):
        return redirect('employee_login')
    context = dashboard_context('employee', settings.WORKER_SHEET_CSV_URL)
    context['worker_records'] = context['sheet_table_rows']
    context['worker_headers'] = context['sheet_headers']
    return render(request, 'employee_dashboard.html', context)
