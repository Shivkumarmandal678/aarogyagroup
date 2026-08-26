import os
import io
import csv
import re
import requests
from datetime import datetime

# Environment Variables बाट URLs लिने
WEB_APP_URL = os.environ.get('GOOGLE_WEB_APP_URL')
CSV_URL = os.environ.get('GOOGLE_SHEET_CSV_URL')
SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '1iRN1kAgDdrfET5DEqKG_ZeCwQiUqmoge4emB_2cbWQg')

# =========================================================================
# HELPER: GOOGLE DRIVE LINK LAI DIRECT IMAGE URL MA BADALNE
# =========================================================================
def format_drive_image(url):
    """Google Drive को Sharing Link लाई सिधै देखिने Direct Image Link मा बदल्छ"""
    if not url:
        return 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'
    
    url = str(url).strip()
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url) or re.search(r'id=([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://lh3.googleusercontent.com/d/{file_id}"
    return url


# =========================================================================
# 1. ADMIN AUTHENTICATION (LOGIN CHECK)
# =========================================================================
def get_admin_by_username(username):
    """Google Sheet को 'Admin' Tab बाट Username र Password जाँच्ने"""
    target_user = str(username).strip().lower()

    # १. Apps Script Web App बाट लिने
    if WEB_APP_URL:
        try:
            res = requests.get(f"{WEB_APP_URL}?action=get_admins", timeout=12, allow_redirects=True)
            if res.status_code == 200:
                data = res.json()
                for user in data:
                    if str(user.get('Username', '')).strip().lower() == target_user:
                        user['Profile_Image'] = format_drive_image(user.get('Profile_Image'))
                        return user
        except Exception as e:
            print("Apps Script Fetch Error:", e)

    # २. Direct Google Sheet CSV Export बाट लिने (Fallback)
    fallback_csv_url = CSV_URL or f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Admin"
    try:
        res = requests.get(fallback_csv_url, timeout=12)
        if res.status_code == 200:
            reader = csv.DictReader(io.StringIO(res.text))
            for row in reader:
                # Keys strip garne
                clean_row = {k.strip(): str(v).strip() for k, v in row.items() if k}
                if clean_row.get('Username', '').lower() == target_user:
                    clean_row['Profile_Image'] = format_drive_image(clean_row.get('Profile_Image'))
                    return clean_row
    except Exception as e:
        print("CSV Read Error:", e)

    return None


# =========================================================================
# 2. ADMIN PASSWORD UPDATE
# =========================================================================
def update_admin_password_sheet(username, new_password):
    """Google Sheet मा गएर नयाँ Password सेभ गर्ने"""
    if not WEB_APP_URL:
        return False
    
    payload = {
        'action': 'change_password',
        'username': str(username).strip(),
        'new_password': str(new_password).strip()
    }
    
    try:
        res = requests.post(WEB_APP_URL, json=payload, timeout=12, allow_redirects=True)
        return res.status_code in [200, 302]
    except Exception as e:
        print("Password Update Error:", e)
        return False


# =========================================================================
# 3. CLIENT BOOKING DATA SAVE (POST)
# =========================================================================
def save_client_booking(data):
    """Client को Booking Google Sheet को 'Booking' Tab मा थप्ने"""
    if not WEB_APP_URL:
        print("GOOGLE_WEB_APP_URL is missing!")
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
        res = requests.post(WEB_APP_URL, json=payload, timeout=12, allow_redirects=True)
        return res.status_code in [200, 302]
    except Exception as e:
        print("Booking Save Error:", e)
        return False


# =========================================================================
# 4. GET ALL CLIENT BOOKINGS (FOR DASHBOARD)
# =========================================================================
def get_all_client_bookings():
    """Admin Dashboard मा देखाउन Booking Tab बाट सबै Data ल्याउने"""
    if WEB_APP_URL:
        try:
            res = requests.get(f"{WEB_APP_URL}?action=get_bookings", timeout=12, allow_redirects=True)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass

    # Fallback CSV for Booking tab
    booking_csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Booking"
    try:
        res = requests.get(booking_csv_url, timeout=12)
        if res.status_code == 200:
            reader = csv.DictReader(io.StringIO(res.text))
            return [row for row in reader]
    except Exception:
        pass

    return []