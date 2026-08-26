import os
import io
import csv
import re
import requests
from datetime import datetime

WEB_APP_URL = os.environ.get('GOOGLE_WEB_APP_URL')
SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '1iRNlkAgDdrfET5DEqKG_ZeCwQiUqmoge4emB_2cbWQg')

# =========================================================================
# HELPER: GOOGLE DRIVE LINK CONVERTER
# =========================================================================
def format_drive_image(url):
    """Google Drive Link लाई Direct Image URL मा बदल्ने"""
    if not url:
        return 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'
    url = str(url).strip()
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url) or re.search(r'id=([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://lh3.googleusercontent.com/d/{file_id}"
    return url

# =========================================================================
# CORE HELPER: SHEET DATA FETCH ENGINE (APPS SCRIPT + CSV DUAL FETCH)
# =========================================================================
def fetch_sheet_rows(sheet_name):
    """कुनै पनि Tab बाट सबै Rows सफासँग ल्याउने"""
    # १. Apps Script Web App बाट
    if WEB_APP_URL:
        try:
            action = "get_admins" if sheet_name == "Admin" else "get_bookings"
            r = requests.get(f"{WEB_APP_URL}?action={action}", timeout=8, allow_redirects=True)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    return [{str(k).strip(): str(v).strip() for k, v in item.items() if k} for item in data]
        except Exception as e:
            print(f"Apps Script Error for {sheet_name}:", e)

    # २. Direct CSV Fallback (१००% ग्यारेन्टी)
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        r = requests.get(csv_url, timeout=8)
        if r.status_code == 200:
            reader = csv.DictReader(io.StringIO(r.text))
            rows = []
            for row in reader:
                clean_row = {str(k).replace('"', '').strip(): str(v).replace('"', '').strip() for k, v in row.items() if k}
                if any(clean_row.values()):
                    rows.append(clean_row)
            return rows
    except Exception as e:
        print(f"CSV Error for {sheet_name}:", e)

    return []

# =========================================================================
# 1. UNIVERSAL AUTHENTICATION (ADMIN / STAFF / ANY USER)
# =========================================================================
def authenticate_user(login_input, password_input):
    """
    Username वा Email दुवैबाट र Admin वा Staff सबैलाई Login गराउने
    """
    login_id = str(login_input).strip().lower()
    password = str(password_input).strip()

    admin_rows = fetch_sheet_rows("Admin")
    for user in admin_rows:
        uname = str(user.get('Username', '')).strip().lower()
        uemail = str(user.get('Email', '')).strip().lower()
        upass = str(user.get('Password', '')).strip()

        # Username वा Email मध्ये एक मिलेमा र Password मिलेमा Login सफल
        if (login_id == uname or login_id == uemail) and (password == upass):
            user['Profile_Image'] = format_drive_image(user.get('Profile_Image'))
            return user

    return None

# =========================================================================
# 2. GET ALL BOOKINGS (FOR DASHBOARD)
# =========================================================================
def get_all_client_bookings():
    """Booking Tab बाट सबै डाटा ल्याउने"""
    return fetch_sheet_rows("Booking")

# =========================================================================
# 3. CHANGE PASSWORD IN GOOGLE SHEET
# =========================================================================
def update_admin_password_sheet(username, new_password):
    if not WEB_APP_URL:
        return False
    payload = {
        'action': 'change_password',
        'username': str(username).strip(),
        'new_password': str(new_password).strip()
    }
    try:
        res = requests.post(WEB_APP_URL, json=payload, timeout=8, allow_redirects=True)
        return res.status_code in [200, 302]
    except Exception:
        return False

# =========================================================================
# 4. SAVE CLIENT BOOKING (POST)
# =========================================================================
def save_client_booking(data):
    if not WEB_APP_URL:
        return False
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
        res = requests.post(WEB_APP_URL, json=payload, timeout=8, allow_redirects=True)
        return res.status_code in [200, 302]
    except Exception:
        return False