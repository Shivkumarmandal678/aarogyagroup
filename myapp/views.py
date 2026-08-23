from django.shortcuts import render
from django.conf import settings

from .google_sheets import GoogleSheetError, fetch_sheet_data


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

# Home view
def home(request):
    return render(request, 'home.html')

# Worker Dashboard view
def worker_dashboard(request):
    return render(request, 'worker_dashboard.html', dashboard_context('worker'))

# Employer Dashboard view
def employer_dashboard(request):
    return render(request, 'employer_dashboard.html', dashboard_context('employer'))
