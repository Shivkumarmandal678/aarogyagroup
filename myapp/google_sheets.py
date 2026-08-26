import os
import io
import csv
import json
import requests
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

WEB_APP_URL = os.environ.get('GOOGLE_WEB_APP_URL')
CSV_URL = os.environ.get('GOOGLE_SHEET_CSV_URL')
SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '1iRN1kAgDdrfET5DEqKG_ZeCwQiUqmoge4emB_2cbWQg')

def get_spreadsheet():
    """Gspread मार्फत Sheet खोल्ने यदि credentials छ भने"""
    try:
        sa_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        if sa_json:
            creds = Credentials.from_service_account_info(json.loads(sa_json), scopes=SCOPES)
            client = gspread.authorize(creds)
            return client.open_by_key(SHEET_ID)
        elif os.path.exists('credentials.json'):
            client = gspread.service_account(filename='credentials.json')
            return client.open_by_key(SHEET_ID)
    except Exception as e:
        print("Gspread connect error:", e)
    return None

# ==========================================
# 1. BOOKING SAVE FUNCTION (POST)
# ==========================================
def save_client_booking(data):
    """Booking data Google Sheet को 'Booking' Tab मा थप्ने"""
    # 1. यदि Google Apps Script URL छ भने (सबैभन्दा छिटो र सरल)
    if WEB_APP_URL:
        payload = {
            'action': 'add_booking',
            'timestamp': datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            'name': data.get('name', ''),
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'service': data.get('service', data.get('department', '')),
            'date': data.get('date', ''),
            'message': data.get('message', ''),
            'status': 'Pending'
        }
        try:
            res = requests.post(WEB_APP_URL, json=payload, timeout=10)
            if res.status_code in [200, 302]:
                return True
        except Exception as e:
            print("Web app post error:", e)

    # 2. Fallback: Gspread मार्फत
    try:
        sh = get_spreadsheet()
        if sh:
            ws = sh.worksheet("Booking")
            row = [
                datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                data.get('name', ''),
                data.get('phone', ''),
                data.get('email', ''),
                data.get('service', data.get('department', '')),
                data.get('date', ''),
                data.get('message', ''),
                'Pending'
            ]
            ws.append_row(row, value_input_option='USER_ENTERED')
            return True
    except Exception as e:
        print("Gspread booking error:", e)

    return False

# ==========================================
# 2. ADMIN AUTHENTICATION (GET & UPDATE)
# ==========================================
def get_admin_by_username(username):
    """Admin Tab बाट Username खोज्ने"""
    # Web app बाट खोज्ने
    if WEB_APP_URL:
        try:
            res = requests.get(f"{WEB_APP_URL}?action=get_admins", timeout=10)
            if res.status_code == 200:
                for user in res.json():
                    if str(user.get('Username', '')).strip().lower() == str(username).strip().lower():
                        return user
        except Exception:
            pass

    # Gspread बाट खोज्ने
    try:
        sh = get_spreadsheet()
        if sh:
            ws = sh.worksheet("Admin")
            for user in ws.get_all_records():
                if str(user.get('Username', '')).strip().lower() == str(username).strip().lower():
                    return user
    except Exception:
        pass

    # CSV बाट खोज्ने
    if CSV_URL:
        try:
            res = requests.get(CSV_URL, timeout=10)
            if res.status_code == 200:
                reader = csv.DictReader(io.StringIO(res.text))
                for row in reader:
                    if str(row.get('Username', '')).strip().lower() == str(username).strip().lower():
                        return row
        except Exception:
            pass

    return None

def update_admin_password_sheet(username, new_password):
    """Google Sheet मा Password Update गर्ने"""
    if WEB_APP_URL:
        try:
            payload = {
                'action': 'change_password',
                'username': username,
                'new_password': new_password
            }
            res = requests.post(WEB_APP_URL, json=payload, timeout=10)
            if res.status_code in [200, 302]:
                return True
        except Exception:
            pass

    try:
        sh = get_spreadsheet()
        if sh:
            ws = sh.worksheet("Admin")
            cell = ws.find(str(username).strip())
            if cell:
                ws.update_cell(cell.row, 2, str(new_password))
                return True
    except Exception:
        pass

    return False

def get_all_client_bookings():
    """Dashboard मा देखाउन Booking Tab बाट डाटा ल्याउने"""
    try:
        sh = get_spreadsheet()
        if sh:
            ws = sh.worksheet("Booking")
            return ws.get_all_records()
    except Exception:
        pass
    return []