import os
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_client():
    """Service Account JSON वा Local File बाट Google Client Authorize गर्ने"""
    sa_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    if sa_json:
        try:
            service_account_info = json.loads(sa_json)
            creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
            return gspread.authorize(creds)
        except Exception as e:
            print("Service account error:", e)

    if os.path.exists('credentials.json'):
        return gspread.service_account(filename='credentials.json')
    return None

def get_spreadsheet():
    client = get_client()
    sheet_id = os.environ.get('GOOGLE_SHEET_ID', '1iRN1kAgDdrfET5DEqKG_ZeCwQiUqmoge4emB_2cbWQg')
    if client:
        return client.open_by_key(sheet_id)
    return None

# ==========================================
# 1. CLIENT / BOOKING FUNCTIONS
# ==========================================

def save_client_booking(data):
    """Client ko Booking Google Sheet (Client Tab) ma save garne"""
    try:
        sh = get_spreadsheet()
        if not sh:
            return False
        worksheet = sh.worksheet("Client")
        
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get('name', ''),
            data.get('phone', ''),
            data.get('email', ''),
            data.get('department', data.get('service', '')),
            data.get('date', ''),
            data.get('message', ''),
            'Pending'
        ]
        worksheet.append_row(row, value_input_option='USER_ENTERED')
        return True
    except Exception as e:
        print("Error saving booking:", e)
        return False

def get_all_clients():
    """Client Tab बाट सबै Booking डाटा ल्याउने (Dashboard मा देखाउन)"""
    try:
        sh = get_spreadsheet()
        if sh:
            worksheet = sh.worksheet("Client")
            return worksheet.get_all_records()
    except Exception as e:
        print("Error fetching clients:", e)
    return []

# ==========================================
# 2. ADMIN & USER AUTHENTICATION
# ==========================================

def get_admin_by_username(username):
    """Admin Tab बाट Username खोज्ने"""
    try:
        sh = get_spreadsheet()
        if not sh:
            return None
        worksheet = sh.worksheet("Admin")
        records = worksheet.get_all_records()
        for user in records:
            if str(user.get('Username', '')).strip().lower() == str(username).strip().lower():
                return user
    except Exception as e:
        print("Error fetching admin:", e)
    return None

def update_admin_password_sheet(username, new_password):
    """Admin Tab मा गएर Password Update गर्ने"""
    try:
        sh = get_spreadsheet()
        if not sh:
            return False
        worksheet = sh.worksheet("Admin")
        
        # Username भएको Cell खोज्ने
        cell = worksheet.find(str(username).strip())
        if cell:
            # Password Column B (Column 2) मा पर्छ
            worksheet.update_cell(cell.row, 2, str(new_password))
            return True
    except Exception as e:
        print("Error updating password in Sheet:", e)
    return False