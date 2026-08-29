import os
import io
import csv
import re
import requests
from datetime import datetime

WEB_APP_URL = os.environ.get('GOOGLE_WEB_APP_URL')
SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '1iRNlkAgDdrfET5DEqKG_ZeCwQiUqmoge4emB_2cbWQg')
DEMO_KEYWORDS = (
    'demo', 'sample', 'fake', 'bot', 'automation', 'script',
    'placeholder', 'lorem', 'dummy', 'trial', 'spam'
)


def _normalize_text(value):
    return re.sub(r'[^a-z0-9]+', ' ', str(value or '').lower()).strip()


def _contains_demo_keyword(value):
    if value is None:
        return False
    text = _normalize_text(value)
    if not text:
        return False
    tokens = set(text.split())
    return bool(tokens & set(DEMO_KEYWORDS))


def looks_like_demo_submission(data):
    if not isinstance(data, dict):
        return True

    email = str(data.get('email', '') or '').strip().lower()
    if email:
        local_part = email.split('@', 1)[0]
        if _contains_demo_keyword(local_part):
            return True

    message = str(data.get('message', '') or '').strip().lower()
    if _contains_demo_keyword(message):
        return True

    name = str(data.get('name', '') or '').strip().lower()
    if name and not email and any(keyword in name for keyword in ('demo', 'sample', 'fake', 'bot', 'spam')):
        return True

    phone = _normalize_text(data.get('phone'))
    if phone in {'1234567890', '0000000000', '1111111111', '9999999999'}:
        return True

    if not any(str(data.get(field, '') or '').strip() for field in ('name', 'phone', 'email', 'service', 'date')):
        return True

    return False

# =========================================================================
# HELPER: GOOGLE DRIVE LINK CONVERTER
# =========================================================================
def format_drive_image(url):
    """Convert a Google Drive link into a direct image URL."""
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
    """Fetch all rows cleanly from any sheet tab."""
    # 1. Apps Script Web App
    if WEB_APP_URL:
        try:
            action = {
                'Admin': 'get_admins',
                'Booking': 'get_bookings',
                'Reports': 'get_reports',
            }.get(sheet_name, f'get_{sheet_name.lower()}')
            r = requests.get(f"{WEB_APP_URL}?action={action}", timeout=8, allow_redirects=True)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    return [{str(k).strip(): str(v).strip() for k, v in item.items() if k} for item in data]
        except Exception as e:
            print(f"Apps Script Error for {sheet_name}:", e)

    # 2. Direct CSV fallback
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
    Allow login by username or email for admin and staff accounts.
    """
    login_id = str(login_input).strip().lower()
    password = str(password_input).strip()

    admin_rows = fetch_sheet_rows("Admin")
    for user in admin_rows:
        uname = str(user.get('Username', '')).strip().lower()
        uemail = str(user.get('Email', '')).strip().lower()
        upass = str(user.get('Password', '')).strip()

        # Match either username or email and verify the password.
        if (login_id == uname or login_id == uemail) and (password == upass):
            user['Profile_Image'] = format_drive_image(user.get('Profile_Image'))
            return user

    return None

# =========================================================================
# 2. GET ALL BOOKINGS (FOR DASHBOARD)
# =========================================================================
def get_all_client_bookings():
    """Fetch all booking data from the Booking sheet."""
    return fetch_sheet_rows("Booking")


def get_all_reports():
    return fetch_sheet_rows("Reports")


def post_sheet_action(action, data=None):
    if not WEB_APP_URL:
        return False
    payload = {'action': action, **(data or {})}
    try:
        response = requests.post(WEB_APP_URL, json=payload, timeout=8, allow_redirects=True)
        if response.status_code not in [200, 201, 302]:
            return False
        try:
            result = response.json()
            return result.get('success', True) if isinstance(result, dict) else True
        except ValueError:
            return True
    except Exception:
        return False

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
    if not isinstance(data, dict):
        return False

    if looks_like_demo_submission(data):
        return False

    required = ['name', 'phone', 'email', 'passport_number', 'address', 'service', 'country', 'passport_copy', 'date', 'message']
    if any(not str(data.get(field, '')).strip() for field in required):
        return False

    payload = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        'name': data.get('name', ''),
        'phone': data.get('phone', ''),
        'email': data.get('email', ''),
        'address': data.get('address', ''),
        'passport_number': data.get('passport_number', ''),
        'lot_number': data.get('lot_number', ''),
        'service': data.get('service', data.get('department', '')),
        'country': data.get('country', ''),
        'passport_copy': data.get('passport_copy', ''),
        'date': data.get('date', ''),
        'message': data.get('message', ''),
        'status': 'Pending'
    }
    return post_sheet_action('add_booking', payload)