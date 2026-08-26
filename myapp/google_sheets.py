import os
import io
import csv
import re
import requests
from datetime import datetime

WEB_APP_URL = os.environ.get('GOOGLE_WEB_APP_URL')
SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '1iRNlkAgDdrfET5DEqKG_ZeCwQiUqmoge4emB_2cbWQg')

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
# 1. GET ALL BOOKINGS (UNLIMITED LIVE FETCH)
# =========================================================================
def get_all_client_bookings():
    """Booking Tab बाट सबै डाटा लोड गर्ने (Apps Script + CSV Dual Engine)"""
    # १. Apps Script बाट
    if WEB_APP_URL:
        try:
            res = requests.get(f"{WEB_APP_URL}?action=get_bookings", timeout=10, allow_redirects=True)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception as e:
            print("Apps script fetch error:", e)

    # २. Direct CSV Fallback (१००% ग्यारेन्टी)
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Booking"
    try:
        res = requests.get(csv_url, timeout=10)
        if res.status_code == 200:
            reader = csv.DictReader(io.StringIO(res.text))
            bookings = []
            for row in reader:
                clean_row = {str(k).replace('"', '').strip(): str(v).replace('"', '').strip() for k, v in row.items() if k}
                # खाली row हटाउने
                if clean_row.get('Name') or clean_row.get('Phone'):
                    bookings.append(clean_row)
            return bookings
    except Exception as e:
        print("CSV Booking fetch error:", e)

    return []

# =========================================================================
# 2. ADMIN AUTHENTICATION (ALL ADMINS / ROLES SUPPORT)
# =========================================================================
def get_admin_by_username(username):
    """Admin Tab बाट Username खोज्ने"""
    target = str(username).strip().lower()

    # Apps Script
    if WEB_APP_URL:
        try:
            res = requests.get(f"{WEB_APP_URL}?action=get_admins", timeout=10, allow_redirects=True)
            if res.status_code == 200:
                for user in res.json():
                    if str(user.get('Username', '')).strip().lower() == target:
                        user['Profile_Image'] = format_drive_image(user.get('Profile_Image'))
                        return user
        except Exception:
            pass

    # Direct CSV
    admin_csv = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Admin"
    try:
        res = requests.get(admin_csv, timeout=10)
        if res.status_code == 200:
            reader = csv.DictReader(io.StringIO(res.text))
            for row in reader:
                clean_row = {str(k).replace('"', '').strip(): str(v).replace('"', '').strip() for k, v in row.items() if k}
                if clean_row.get('Username', '').lower() == target:
                    clean_row['Profile_Image'] = format_drive_image(clean_row.get('Profile_Image'))
                    return clean_row
    except Exception:
        pass

    return None

# =========================================================================
# 3. CHANGE PASSWORD
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
        res = requests.post(WEB_APP_URL, json=payload, timeout=10, allow_redirects=True)
        return res.status_code in [200, 302]
    except Exception:
        return False

# =========================================================================
# 4. SAVE NEW BOOKING
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
        res = requests.post(WEB_APP_URL, json=payload, timeout=10, allow_redirects=True)
        return res.status_code in [200, 302]
    except Exception:
        return False