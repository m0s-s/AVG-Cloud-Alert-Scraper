import os
import platform
import requests
import json
import time
from datetime import datetime
from dateutil import parser
import ctypes

# CONFIGURATION
CLIENT_ID = 'INSERT_CLIENT_ID'
CLIENT_SECRET = 'INSERT_CLIENT_SECRET'
REGION = 'europe-west3'
BASE_URL = f'https://api-gateway.prod-{REGION}.smbrm.avast.com'
PAGE_SIZE = 50

# CROSS-PLATFORM BASE PATH
if platform.system() == 'Windows':
    from ctypes import windll, create_unicode_buffer

    def get_windows_system_drive():
        buffer = create_unicode_buffer(260)
        windll.kernel32.GetWindowsDirectoryW(buffer, 260)
        return buffer.value[:3]  # e.g., 'C:\'

    BASE_PATH = os.path.join(get_windows_system_drive(), 'avgcloud')
else:
    BASE_PATH = '/opt/avgcloud'

SAVE_DIR = os.path.join(BASE_PATH, 'logs')
LAST_DATE_FILE = os.path.join(BASE_PATH, 'last_created_on.txt')

# CREATE FOLDERS
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LAST_DATE_FILE), exist_ok=True)

# LOAD LAST ALERT TIMESTAMP
if os.path.exists(LAST_DATE_FILE):
    with open(LAST_DATE_FILE, 'r') as f:
        last_created_on = f.read().strip()
else:
    last_created_on = None

def save_last_created_on(timestamp):
    with open(LAST_DATE_FILE, 'w') as f:
        f.write(timestamp)

def get_token():
    print("🔐 Getting access token...")
    url = 'https://business-auth.prod.smbrm.avast.com/token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'console'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    resp = requests.post(url, data=data, headers=headers)
    resp.raise_for_status()
    token = resp.json()['access_token']
    print("✅ Access token received.")
    return token

def get_company_id(token):
    print("🏢 Retrieving company ID...")
    headers = {'Authorization': f'Bearer {token}'}
    url = f'{BASE_URL}/api/v1/users/companies'
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    companies = resp.json().get('data', [])
    if not companies:
        raise Exception("❌ No company found")
    print(f"✅ {len(companies)} companies found.")
    return companies[0]['id']

def get_device_map(token, company_id):
    print("📥 Downloading device list...")
    headers = {'Authorization': f'Bearer {token}'}
    page = 0
    device_map = {}
    while True:
        url = f'{BASE_URL}/api/v1/companies/{company_id}/devices?page={page}&size=100'
        resp = requests.get(url, headers=headers)
        if resp.status_code == 429:
            print("⏳ Rate limited, waiting 5s...")
            time.sleep(5)
            continue
        if resp.status_code == 500:
            print("⚠️ Device API internal server error.")
            break
        resp.raise_for_status()
        data = resp.json().get('data', [])
        if not data:
            break
        for device in data:
            device_id = device.get('id')
            if device_id:
                device_map[device_id] = device
        page += 1
        time.sleep(1)
    print(f"✅ {len(device_map)} devices found.")
    return device_map

def get_alert_detail(token, company_id, alert_id):
    headers = {'Authorization': f'Bearer {token}'}
    url = f'{BASE_URL}/api/v1/companies/{company_id}/alerts/{alert_id}'
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"⚠️ Failed to get alert detail for ID {alert_id}")
        return None

def download_full_alerts(token, company_id):
    print(f"⬇️ Downloading full alerts for company {company_id}...")
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    page = 0
    total = 0

    payload = {
        "sorts": [{"field": "CATEGORY", "direction": "ASC"}]
    }
    if last_created_on:
        payload["createdOnFrom"] = last_created_on

    last_saved = parser.isoparse(last_created_on) if last_created_on else None
    max_created_on = last_saved

    device_map = get_device_map(token, company_id)

    while True:
        url = f'{BASE_URL}/api/v1/companies/{company_id}/alerts/search?page={page}&size={PAGE_SIZE}'
        print(f"📦 Requesting alerts (page {page}) from: {url}")
        response = requests.post(url, headers=headers, json=payload)
        print(f"📄 Status Code: {response.status_code}")

        if response.status_code == 429:
            print("⏳ Too many requests, waiting 5 seconds...")
            time.sleep(5)
            continue

        response.raise_for_status()
        data = response.json()
        alerts = data.get('data', [])

        if not alerts:
            print("🚫 No new alerts found.")
            break

        for alert in alerts:
            alert_id = alert.get('id')
            created_on = alert.get('createdOn')
            current_created = parser.isoparse(created_on)

            if last_saved and current_created <= last_saved:
                continue

            if not max_created_on or current_created > max_created_on:
                max_created_on = current_created

            detail = get_alert_detail(token, company_id, alert_id)
            if detail:
                device_id = detail.get('deviceId')
                device_info = device_map.get(device_id, {}) if device_id else {}
                combined = {
                    "alert_data": detail,
                    "device_info": device_info
                }
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                name = detail.get('name', 'unknown')
                filename = f"{name}_{alert_id}_{timestamp}.txt"
                filepath = os.path.join(SAVE_DIR, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(combined, separators=(',', ':')))
                print(f"✅ Saved: {filename}")
                total += 1
                time.sleep(0.3)

        if not data.get('page', {}).get('hasNext', False):
            break

        page += 1
        time.sleep(1)

    if max_created_on:
        save_last_created_on(max_created_on.isoformat())

    print(f"🎉 Download complete. Total alerts saved: {total}")

def main():
    token = get_token()
    company_id = get_company_id(token)
    download_full_alerts(token, company_id)

if __name__ == '__main__':
    main()
