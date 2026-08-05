"""
Test Swagger Documentation
"""

import requests

print("=" * 60)
print("📚 Testing Swagger Documentation")
print("=" * 60)

BASE_URL = "http://localhost:5001"

# Check Swagger UI
print("\n📖 Swagger UI:")
print(f"   URL: {BASE_URL}/docs/")
print("   Open in browser to view API documentation")

# Check API spec JSON
print("\n📋 API Specification:")
try:
    response = requests.get(f"{BASE_URL}/apispec.json")
    if response.status_code == 200:
        spec = response.json()
        print(f"   ✅ API Spec loaded")
        print(f"   📊 Total APIs: {len(spec.get('paths', {}))}")
        print(f"   📝 Tags: {len(spec.get('tags', []))}")
        
        # Count endpoints by tag
        paths = spec.get('paths', {})
        endpoints = {}
        for path, methods in paths.items():
            for method, details in methods.items():
                tag = details.get('tags', ['Uncategorized'])[0]
                endpoints[tag] = endpoints.get(tag, 0) + 1
        
        print("\n   📊 Endpoints by Tag:")
        for tag, count in sorted(endpoints.items(), key=lambda x: x[1], reverse=True):
            print(f"      - {tag}: {count}")
    else:
        print(f"   ❌ Failed to load API spec: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ Swagger test complete!")
print("=" * 60)
