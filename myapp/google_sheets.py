import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # service_account.json file ka path
    creds = ServiceAccountCredentials.from_json_keyfile_name(BASE_DIR / 'service_account.json', scope)
    client = gspread.authorize(creds)
    
    # Sheet name: Admin_Login_System
    sheet = client.open("Admin_Login_System").sheet1
    return sheet

def register_user_to_sheet(data):
    sheet = get_sheet()
    # Sheet Columns: [Username, Email, Phone, Address, Password]
    sheet.append_row([
        data['username'],
        data['email'],
        data['phone'],
        data['address'],
        data['password']
    ])

def get_user_by_username(username):
    sheet = get_sheet()
    records = sheet.get_all_records()
    for row in records:
        if str(row.get('Username')).strip() == username.strip():
            return row
    return None

def update_user_password(email, new_password):
    sheet = get_sheet()
    records = sheet.get_all_records()
    for idx, row in enumerate(records, start=2): # Header offset +1
        if str(row.get('Email')).strip() == email.strip():
            sheet.update_cell(idx, 5, new_password) # Column 5 = Password
            return True
    return False