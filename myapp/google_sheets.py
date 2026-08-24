import os
import csv
import requests
import io

# 1. Read Data (Using CSV URL)
def get_sheet_data_from_csv():
    csv_url = os.environ.get('GOOGLE_SHEET_CSV_URL')
    response = requests.get(csv_url)
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        csv_file = io.StringIO(content)
        return list(csv.DictReader(csv_file))
    return []

def get_user_by_username(username):
    records = get_sheet_data_from_csv()
    for row in records:
        if str(row.get('Username', '')).strip().lower() == username.strip().lower():
            return row
    return None

# 2. Write/Register User (Using Google Web App URL)
def register_user_to_sheet(data):
    web_app_url = os.environ.get('GOOGLE_WEB_APP_URL')
    payload = {
        "action": "register",
        "username": data['username'],
        "email": data['email'],
        "phone": data['phone'],
        "address": data['address'],
        "password": data['password']
    }
    response = requests.post(web_app_url, json=payload)
    return response.json()

# 3. Update Password (Using Google Web App URL)
def update_user_password(email, new_password):
    web_app_url = os.environ.get('GOOGLE_WEB_APP_URL')
    payload = {
        "action": "update_password",
        "email": email,
        "new_password": new_password
    }
    response = requests.post(web_app_url, json=payload)
    res_data = response.json()
    return res_data.get('status') == 'success'