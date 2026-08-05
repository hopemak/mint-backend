"""
Test MongoDB Atlas Connection - With Correct Credentials
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Get connection string
mongodb_uri = os.environ.get('MONGODB_URI')
db_name = os.environ.get('MONGODB_DB', 'mint_platform')

print("=" * 60)
print("🗄️ Testing MongoDB Atlas Connection")
print("=" * 60)

if not mongodb_uri:
    print("\n❌ MONGODB_URI not found in .env file!")
    exit(1)

# Hide password for security
print(f"\n📊 Database: {db_name}")

try:
    print("\n🔄 Connecting to MongoDB Atlas...")
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    
    # Test connection
    client.admin.command('ping')
    print("✅ Connection successful!")
    
    # Get database
    db = client[db_name]
    
    # List collections
    collections = db.list_collection_names()
    print(f"\n📁 Collections: {collections if collections else 'None (empty database)'}")
    
    # Insert test data
    test_collection = db.test_connection
    test_collection.insert_one({
        'test': True,
        'timestamp': '2024-07-25',
        'message': 'MongoDB Atlas connection successful!'
    })
    print("✅ Test data inserted successfully!")
    
    # Show connection info
    print(f"\n📊 Connection Info:")
    print(f"   - Database: {db_name}")
    print(f"   - Collections: {len(collections)}")
    
    client.close()
    print("\n✅ MongoDB Atlas connection test passed!")
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\n⚠️ Please check:")
    print("   1. Network access (IP whitelist)")
    print("   2. Connection string format")
    print("\n💡 Go to MongoDB Atlas > Network Access > Add IP Address")
    print("   Add: 0.0.0.0/0 (for testing)")
