"""
MongoDB Database Connection - With Test Mode Support
"""

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    """MongoDB database connection manager"""
    
    _instance = None
    _client = None
    _db = None
    _disabled = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def connect(self):
        """Connect to MongoDB Atlas or fallback to in-memory"""
        # Check if MongoDB is disabled (for testing)
        if os.environ.get('FLASK_ENV') == 'testing':
            logger.info("🧪 Test mode: MongoDB disabled, using in-memory storage")
            self._disabled = True
            return None
        
        try:
            # Get connection string from environment
            mongodb_uri = os.environ.get('MONGODB_URI')
            
            if not mongodb_uri:
                logger.warning("⚠️ No MONGODB_URI found, using in-memory storage")
                self._disabled = True
                return None
            
            logger.info("🔄 Connecting to MongoDB Atlas...")
            
            self._client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self._client.admin.command('ping')
            
            db_name = os.environ.get('MONGODB_DB', 'mint_platform')
            self._db = self._client[db_name]
            
            logger.info(f"✅ Connected to MongoDB Atlas: {db_name}")
            self._disabled = False
            return self._db
            
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            logger.info("⚠️ Continuing with in-memory storage as fallback...")
            self._disabled = True
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            logger.info("⚠️ Continuing with in-memory storage as fallback...")
            self._disabled = True
            return None
    
    def get_db(self):
        """Get database instance"""
        if self._disabled:
            return None
        if self._db is None:
            self.connect()
        return self._db
    
    def get_collection(self, name):
        """Get a collection"""
        if self._disabled:
            return None
        db = self.get_db()
        if db is None:
            return None
        return db[name]
    
    def is_available(self):
        """Check if MongoDB is available"""
        return not self._disabled and self._db is not None
    
    def create_indexes(self):
        """Create indexes for better performance"""
        if self._disabled:
            return
        
        db = self.get_db()
        if db is None:
            return
        
        try:
            # User indexes
            db.users.create_index('email', unique=True)
            db.users.create_index('role')
            db.users.create_index('status')
            
            # Startup indexes
            db.startups.create_index('startup_id', unique=True)
            db.startups.create_index('user_id')
            db.startups.create_index('sector')
            db.startups.create_index('status')
            db.startups.create_index('created_at')
            
            # Evaluation indexes
            db.evaluations.create_index('startup_id', unique=True)
            db.evaluations.create_index('evaluator_id')
            db.evaluations.create_index('evaluation_date')
            
            # Funding indexes
            db.funding_requests.create_index('request_id', unique=True)
            db.funding_requests.create_index('startup_id')
            db.funding_requests.create_index('status')
            
            # Grant indexes
            db.grants.create_index('grant_id', unique=True)
            db.grants.create_index('sectors')
            db.grants.create_index('deadline')
            
            # Mentor indexes
            db.mentors.create_index('mentor_id', unique=True)
            db.mentors.create_index('user_id')
            db.mentors.create_index('expertise_areas')
            
            # Document indexes
            db.documents.create_index('document_id', unique=True)
            db.documents.create_index('user_id')
            
            logger.info("✅ Database indexes created")
        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")
    
    def close(self):
        """Close connection"""
        if self._client:
            self._client.close()
            logger.info("✅ MongoDB connection closed")

# Singleton instance
db = Database()

# Helper functions
def get_collection(name):
    """Get a collection - returns None if MongoDB is disabled"""
    return db.get_collection(name)

def get_db():
    return db.get_db()

def init_db():
    """Initialize database connection and indexes"""
    try:
        db.connect()
        db.create_indexes()
        if db.is_available():
            logger.info("✅ Database initialized successfully")
        else:
            logger.info("ℹ️ Using in-memory storage fallback")
        return db.is_available()
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.info("⚠️ Continuing with in-memory storage as fallback...")
        return False

def is_db_available():
    """Check if database is available"""
    return db.is_available()

# Collections
USERS_COLLECTION = 'users'
STARTUPS_COLLECTION = 'startups'
EVALUATIONS_COLLECTION = 'evaluations'
FUNDING_REQUESTS_COLLECTION = 'funding_requests'
FUNDING_DISBURSEMENTS_COLLECTION = 'funding_disbursements'
GRANTS_COLLECTION = 'grants'
GRANT_APPLICATIONS_COLLECTION = 'grant_applications'
MENTORS_COLLECTION = 'mentors'
DOCUMENTS_COLLECTION = 'documents'
ANALYTICS_COLLECTION = 'analytics'
AUDIT_LOGS_COLLECTION = 'audit_logs'

__all__ = [
    'db',
    'get_db',
    'get_collection',
    'init_db',
    'is_db_available',
    'USERS_COLLECTION',
    'STARTUPS_COLLECTION',
    'EVALUATIONS_COLLECTION',
    'FUNDING_REQUESTS_COLLECTION',
    'FUNDING_DISBURSEMENTS_COLLECTION',
    'GRANTS_COLLECTION',
    'GRANT_APPLICATIONS_COLLECTION',
    'MENTORS_COLLECTION',
    'DOCUMENTS_COLLECTION',
    'ANALYTICS_COLLECTION',
    'AUDIT_LOGS_COLLECTION'
]
