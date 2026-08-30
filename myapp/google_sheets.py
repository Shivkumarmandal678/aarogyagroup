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

def format_drive_image(url):
    """Convert Google Drive link to direct display image URL."""
    if not url:
        return 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'
    url = str(url).strip()
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url) or re.search(r'id=([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://lh3.googleusercontent.com/d/{file_id}"
    return url

def fetch_sheet_rows(sheet_name):
    """Fetch all rows cleanly from any sheet tab."""
    if WEB_APP_URL:
        try:
            action = {
                'Admin': 'get_admins',
                'Booking': 'get_bookings',
                'Reports': 'get_reports',
                'Chatbot': 'get_chatbot',
            }.get(sheet_name, f'get_{sheet_name.lower()}')
            r = requests.get(f"{WEB_APP_URL}?action={action}", timeout=8, allow_redirects=True)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    return [{str(k).strip(): str(v).strip() for k, v in item.items() if k} for item in data]
        except Exception as e:
            print(f"Apps Script Error for {sheet_name}:", e)

    # Direct CSV fallback
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

def authenticate_user(login_input, password_input):
    """Allow login by username or email for admin and staff accounts."""
    login_id = str(login_input).strip().lower()
    password = str(password_input).strip()

    admin_rows = fetch_sheet_rows("Admin")
    for user in admin_rows:
        uname = str(user.get('Username', '')).strip().lower()
        uemail = str(user.get('Email', '')).strip().lower()
        upass = str(user.get('Password', '')).strip()

        if (login_id == uname or login_id == uemail) and (password == upass):
            user['Profile_Image'] = format_drive_image(user.get('Profile_Image'))
            return user
    return None

def get_all_client_bookings():
    return fetch_sheet_rows("Booking")

def get_all_reports():
    return fetch_sheet_rows("Reports")

def get_chatbot_qa_list():
    """Fetch custom Q&A messages live from the Chatbot tab of Google Sheet."""
    if WEB_APP_URL:
        try:
            r = requests.get(f"{WEB_APP_URL}?action=get_chatbot", timeout=6)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception as e:
            print("Chatbot fetch error:", e)

    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Chatbot"
    try:
        r = requests.get(csv_url, timeout=6)
        if r.status_code == 200:
            reader = csv.reader(io.StringIO(r.text))
            rows = list(reader)
            if len(rows) > 1:
                qa_list = []
                for row in rows[1:]:
                    if len(row) >= 2 and row[0].strip() and row[1].strip():
                        qa_list.append({
                            'keywords': row[0].strip().lower(),
                            'answer': row[1].strip(),
                            'button': row[2].strip() if len(row) > 2 else ''
                        })
                if qa_list:
                    return qa_list
    except Exception as e:
        print("Chatbot CSV error:", e)

    return [
        {"keywords": "service, services, training, course", "answer": "We provide medical biometric orientation, pre-departure training, document guidance, and worker support.", "button": "Our Services"},
        {"keywords": "branch, location, where, office", "answer": "Our branches are located in Lahan, Mirchaiya, Janakpur, and Kathmandu.", "button": "Our Branches"},
        {"keywords": "batch, schedule, time, sunday, tuesday, thursday", "answer": "A new batch runs three days each week: Sunday, Tuesday, and Thursday from 9:00 AM to 6:00 PM.", "button": "Batch Schedule"},
        {"keywords": "contact, phone, call, number, email", "answer": "Branch phones: Lahan 9801196900, Mirchaiya 9801596900, Janakpur 9801196900. Email: aarogyamc@gmail.com", "button": "Contact Details"},
        {"keywords": "default", "answer": "Please ask about our services, medical orientation, training, branches, or call 9801196900.", "button": ""}
    ]

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

def save_client_booking(data):
    if not isinstance(data, dict) or looks_like_demo_submission(data):
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