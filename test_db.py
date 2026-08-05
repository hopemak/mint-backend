"""
Test MongoDB Atlas Connection
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Get connection string
mongodb_uri = os.environ.get(
    'MONGODB_URI',
    'mongodb+srv://abdi:pass@cluster0.l1yycqo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
)
db_name = os.environ.get('MONGODB_DB', 'mint_platform')

print("=" * 60)
print("🗄️ Testing MongoDB Atlas Connection")
print("=" * 60)

print(f"\n📊 Connection URI: {mongodb_uri[:50]}...")
print(f"📊 Database: {db_name}")

try:
    # Connect
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
    
    # Show connection info
    print(f"\n📊 Connection Info:")
    print(f"   - Host: {client.address}")
    print(f"   - Database: {db_name}")
    print(f"   - Collections: {len(collections)}")
    
    client.close()
    print("\n✅ MongoDB Atlas connection test passed!")
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\n⚠️ Please check:")
    print("   1. Your MongoDB Atlas username and password")
    print("   2. Network access (IP whitelist)")
    print("   3. Connection string format")
