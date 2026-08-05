"""
Database Models / Schemas
"""

from datetime import datetime
from typing import Optional, List, Dict

class User:
    """User model"""
    
    @staticmethod
    def create(email: str, password: str, full_name: str, role: str, **kwargs):
        return {
            'email': email,
            'password': password,
            'full_name': full_name,
            'role': role,
            'status': 'active',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'last_login': None,
            **kwargs
        }

class Startup:
    """Startup model"""
    
    @staticmethod
    def create(user_id: str, business_name: str, sector: str, **kwargs):
        return {
            'user_id': user_id,
            'business_name': business_name,
            'sector': sector,
            'status': 'submitted',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'application_date': datetime.utcnow(),
            **kwargs
        }

class Evaluation:
    """Evaluation model"""
    
    @staticmethod
    def create(startup_id: str, evaluator_id: str, scores: Dict, **kwargs):
        return {
            'startup_id': startup_id,
            'evaluator_id': evaluator_id,
            'scores': scores,
            'evaluation_date': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            **kwargs
        }

class FundingRequest:
    """Funding request model"""
    
    @staticmethod
    def create(startup_id: str, user_id: str, amount: float, purpose: str, stage: str, **kwargs):
        return {
            'startup_id': startup_id,
            'user_id': user_id,
            'amount': amount,
            'purpose': purpose,
            'stage': stage,
            'status': 'pending',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            **kwargs
        }

class Grant:
    """Grant model"""
    
    @staticmethod
    def create(grant_name: str, program: str, max_amount: float, min_amount: float, deadline: str, **kwargs):
        return {
            'grant_name': grant_name,
            'program': program,
            'max_amount': max_amount,
            'min_amount': min_amount,
            'deadline': deadline,
            'status': 'active',
            'funds_allocated': 0,
            'funds_remaining': max_amount,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            **kwargs
        }

class Mentor:
    """Mentor model"""
    
    @staticmethod
    def create(user_id: str, full_name: str, expertise_areas: List[str], years_experience: int, **kwargs):
        return {
            'user_id': user_id,
            'full_name': full_name,
            'expertise_areas': expertise_areas,
            'years_experience': years_experience,
            'rating': 0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            **kwargs
        }

class Document:
    """Document model"""
    
    @staticmethod
    def create(user_id: str, filename: str, file_path: str, file_type: str, **kwargs):
        return {
            'user_id': user_id,
            'filename': filename,
            'file_path': file_path,
            'file_type': file_type,
            'uploaded_at': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            **kwargs
        }

__all__ = [
    'User',
    'Startup',
    'Evaluation',
    'FundingRequest',
    'Grant',
    'Mentor',
    'Document'
]
