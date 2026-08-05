"""
Test Audit Logging System
"""

import requests
import json

BASE_URL = "http://localhost:5001"

print("=" * 60)
print("🔍 Testing Audit Logging System")
print("=" * 60)

# 1. Register a user
print("\n1️⃣ Registering user...")
register_data = {
    "email": "testaudit@mint.com",
    "password": "test123",
    "full_name": "Test Audit User",
    "role": "founder"
}
response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json().get('message')}")

# 2. Login
print("\n2️⃣ Logging in...")
login_data = {
    "email": "testaudit@mint.com",
    "password": "test123"
}
response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
cookies = response.cookies
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json().get('message')}")

# 3. Create a startup
print("\n3️⃣ Creating startup...")
startup_data = {
    "business_name": "Audit Test Startup",
    "sector": "Technology"
}
response = requests.post(f"{BASE_URL}/api/startups", json=startup_data, cookies=cookies)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    startup = response.json().get('data', {})
    print(f"   Startup ID: {startup.get('startup_id')}")

# 4. Check audit logs (admin only)
print("\n4️⃣ Admin login for audit logs...")
admin_data = {
    "email": "admin@mint.gov",
    "password": "admin123"
}
response = requests.post(f"{BASE_URL}/api/auth/login", json=admin_data)
admin_cookies = response.cookies
print(f"   Admin Login Status: {response.status_code}")

if response.status_code == 200:
    print("\n5️⃣ Getting audit summary...")
    response = requests.get(f"{BASE_URL}/api/audit/summary", cookies=admin_cookies)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json().get('data', {})
        print(f"   Total Logs: {data.get('total_logs')}")
        print(f"   Unique Actions: {data.get('unique_actions')}")
        print(f"   Recent 24h: {data.get('recent_24h')}")
        
    print("\n6️⃣ Getting recent audit logs...")
    response = requests.get(f"{BASE_URL}/api/audit/logs?limit=10", cookies=admin_cookies)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json().get('data', {})
        logs = data.get('logs', [])
        print(f"   Logs found: {len(logs)}")
        for log in logs[:3]:
            print(f"   - {log.get('timestamp')}: {log.get('action')} by {log.get('user_id', 'system')}")

print("\n" + "=" * 60)
print("✅ Audit logging test complete!")
print("=" * 60)
