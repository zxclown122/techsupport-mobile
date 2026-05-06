import requests
from kivy.storage.jsonstore import JsonStore

store = JsonStore('data.json')
API_BASE = "http://80.242.57.175:8000"

def login(login, password):
    try:
        r = requests.post(f"{API_BASE}/auth/login", json={"login": login, "password": password}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            store.put('auth', token=data['access_token'], user=data['user'])
            return True, data
        else:
            return False, r.json().get('detail', 'Ошибка входа')
    except Exception as e:
        return False, str(e)

def get_current_user():
    if store.exists('auth'):
        return store.get('auth')['user']
    return None

def get_user_role():
    user = get_current_user()
    return user['role'] if user else None

def get_token():
    if store.exists('auth'):
        return store.get('auth')['token']
    return None

def auth_headers():
    token = get_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def create_ticket(title, description, priority, type_):
    headers = auth_headers()
    if not headers:
        return False, "Не авторизован"
    r = requests.post(f"{API_BASE}/tickets", json={"title": title, "description": description, "priority": priority, "type": type_}, headers=headers)
    if r.status_code == 201:
        return True, r.json()
    return False, r.text

def get_tickets(my_only=False, status=None, page=1):
    headers = auth_headers()
    if not headers:
        return None
    params = {"page": page, "limit": 20}
    if status:
        params["status"] = status
    if my_only:
        params["my_only"] = "true"
    r = requests.get(f"{API_BASE}/tickets", params=params, headers=headers)
    if r.status_code == 200:
        return r.json()
    return None

def get_ticket_details(ticket_id):
    headers = auth_headers()
    if not headers:
        return None
    r = requests.get(f"{API_BASE}/tickets/{ticket_id}", headers=headers)
    if r.status_code == 200:
        return r.json()
    return None

def add_comment(ticket_id, text):
    headers = auth_headers()
    if not headers:
        return False, None
    r = requests.post(f"{API_BASE}/tickets/{ticket_id}/comments", json={"text": text}, headers=headers)
    if r.status_code == 201:
        return True, r.json()
    return False, None

def logout():
    if store.exists('auth'):
        store.delete('auth')
