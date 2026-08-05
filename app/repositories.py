"""
Database Repository Layer
Handles all database operations
"""

from datetime import datetime
import uuid
from typing import Dict, List, Optional
from .database import get_collection
from .models import User, Startup, Evaluation, FundingRequest, Grant, Mentor, Document

class UserRepository:
    """User database operations"""
    
    @staticmethod
    def create(user_data: Dict) -> Dict:
        collection = get_collection('users')
        user_data['_id'] = str(uuid.uuid4())
        user_data['created_at'] = datetime.utcnow()
        user_data['updated_at'] = datetime.utcnow()
        result = collection.insert_one(user_data)
        user_data['id'] = user_data['_id']
        del user_data['_id']
        return user_data
    
    @staticmethod
    def find_by_email(email: str) -> Optional[Dict]:
        collection = get_collection('users')
        result = collection.find_one({'email': email})
        if result:
            result['id'] = str(result['_id'])
            del result['_id']
        return result
    
    @staticmethod
    def find_by_id(user_id: str) -> Optional[Dict]:
        collection = get_collection('users')
        try:
            from bson import ObjectId
            result = collection.find_one({'_id': ObjectId(user_id)})
        except:
            result = collection.find_one({'id': user_id})
        if result:
            result['id'] = str(result['_id'])
            del result['_id']
        return result
    
    @staticmethod
    def find_all() -> List[Dict]:
        collection = get_collection('users')
        results = collection.find()
        users = []
        for doc in results:
            doc['id'] = str(doc['_id'])
            del doc['_id']
            users.append(doc)
        return users
    
    @staticmethod
    def update(user_id: str, data: Dict) -> Dict:
        collection = get_collection('users')
        data['updated_at'] = datetime.utcnow()
        try:
            from bson import ObjectId
            result = collection.find_one_and_update(
                {'_id': ObjectId(user_id)},
                {'$set': data},
                return_document=True
            )
        except:
            result = collection.find_one_and_update(
                {'id': user_id},
                {'$set': data},
                return_document=True
            )
        if result:
            result['id'] = str(result['_id'])
            del result['_id']
        return result

class StartupRepository:
    """Startup database operations"""
    
    @staticmethod
    def create(startup_data: Dict) -> Dict:
        collection = get_collection('startups')
        startup_data['_id'] = str(uuid.uuid4())
        startup_data['created_at'] = datetime.utcnow()
        startup_data['updated_at'] = datetime.utcnow()
        result = collection.insert_one(startup_data)
        startup_data['id'] = startup_data['_id']
        del startup_data['_id']
        return startup_data
    
    @staticmethod
    def find_by_id(startup_id: str) -> Optional[Dict]:
        collection = get_collection('startups')
        result = collection.find_one({'startup_id': startup_id})
        if result:
            result['id'] = str(result['_id'])
            del result['_id']
        return result
    
    @staticmethod
    def find_by_user(user_id: str) -> List[Dict]:
        collection = get_collection('startups')
        results = collection.find({'user_id': user_id})
        startups = []
        for doc in results:
            doc['id'] = str(doc['_id'])
            del doc['_id']
            startups.append(doc)
        return startups
    
    @staticmethod
    def find_all(filters: Dict = None) -> List[Dict]:
        collection = get_collection('startups')
        if filters:
            results = collection.find(filters)
        else:
            results = collection.find()
        startups = []
        for doc in results:
            doc['id'] = str(doc['_id'])
            del doc['_id']
            startups.append(doc)
        return startups
    
    @staticmethod
    def update(startup_id: str, data: Dict) -> Dict:
        collection = get_collection('startups')
        data['updated_at'] = datetime.utcnow()
        result = collection.find_one_and_update(
            {'startup_id': startup_id},
            {'$set': data},
            return_document=True
        )
        if result:
            result['id'] = str(result['_id'])
            del result['_id']
        return result

class EvaluationRepository:
    """Evaluation database operations"""
    
    @staticmethod
    def create(evaluation_data: Dict) -> Dict:
        collection = get_collection('evaluations')
        evaluation_data['_id'] = str(uuid.uuid4())
        evaluation_data['created_at'] = datetime.utcnow()
        evaluation_data['updated_at'] = datetime.utcnow()
        result = collection.insert_one(evaluation_data)
        evaluation_data['id'] = evaluation_data['_id']
        del evaluation_data['_id']
        return evaluation_data
    
    @staticmethod
    def find_by_startup(startup_id: str) -> Optional[Dict]:
        collection = get_collection('evaluations')
        result = collection.find_one({'startup_id': startup_id})
        if result:
            result['id'] = str(result['_id'])
            del result['_id']
        return result

class FundingRequestRepository:
    """Funding request database operations"""
    
    @staticmethod
    def create(request_data: Dict) -> Dict:
        collection = get_collection('funding_requests')
        request_data['_id'] = str(uuid.uuid4())
        request_data['created_at'] = datetime.utcnow()
        request_data['updated_at'] = datetime.utcnow()
        result = collection.insert_one(request_data)
        request_data['id'] = request_data['_id']
        del request_data['_id']
        return request_data
    
    @staticmethod
    def find_by_id(request_id: str) -> Optional[Dict]:
        collection = get_collection('funding_requests')
        result = collection.find_one({'request_id': request_id})
        if result:
            result['id'] = str(result['_id'])
            del result['_id']
        return result
    
    @staticmethod
    def find_by_startup(startup_id: str) -> List[Dict]:
        collection = get_collection('funding_requests')
        results = collection.find({'startup_id': startup_id})
        requests = []
        for doc in results:
            doc['id'] = str(doc['_id'])
            del doc['_id']
            requests.append(doc)
        return requests
    
    @staticmethod
    def find_all(filters: Dict = None) -> List[Dict]:
        collection = get_collection('funding_requests')
        if filters:
            results = collection.find(filters)
        else:
            results = collection.find()
        requests = []
        for doc in results:
            doc['id'] = str(doc['_id'])
            del doc['_id']
            requests.append(doc)
        return requests
    
    @staticmethod
    def update(request_id: str, data: Dict) -> Dict:
        collection = get_collection('funding_requests')
        data['updated_at'] = datetime.utcnow()
        result = collection.find_one_and_update(
            {'request_id': request_id},
            {'$set': data},
            return_document=True
        )
        if result:
            result['id'] = str(result['_id'])
            del result['_id']
        return result

# Add other repositories for Grants, Mentors, Documents...
# I'll create the remaining ones in the next step.
