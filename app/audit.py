"""
Audit Logging System
Tracks all actions in the platform
"""

import json
from datetime import datetime
from functools import wraps
from flask import request, g
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.database import get_collection

AUDIT_COLLECTION = 'audit_logs'

def log_action(action, details=None, status='success', error=None):
    """Log an action to the audit log"""
    try:
        user_id = get_jwt_identity() if hasattr(g, 'jwt_user_id') else None
        
        # Get request details
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        method = request.method if request else None
        path = request.path if request else None
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'action': action,
            'details': details,
            'status': status,
            'error': error,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'method': method,
            'path': path
        }
        
        collection = get_collection(AUDIT_COLLECTION)
        collection.insert_one(log_entry)
        
        return log_entry
    except Exception as e:
        # Don't let audit logging failures break the main flow
        print(f"⚠️ Audit log error: {e}")
        return None

def audit(action_template):
    """Decorator to automatically log actions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user ID if available
            try:
                user_id = get_jwt_identity()
                g.jwt_user_id = user_id
            except:
                g.jwt_user_id = None
            
            # Execute the function
            try:
                result = f(*args, **kwargs)
                
                # Extract details from request/response
                details = {
                    'method': request.method,
                    'path': request.path,
                    'args': dict(request.args),
                    'form': dict(request.form) if request.form else {},
                    'json': request.get_json() if request.is_json else {}
                }
                
                # Check if result contains data to log
                if hasattr(result, 'get_json'):
                    response_data = result.get_json()
                    if response_data and 'data' in response_data:
                        details['response_data'] = response_data['data']
                
                # Log success
                log_action(
                    action=action_template,
                    details=details,
                    status='success'
                )
                
                return result
                
            except Exception as e:
                # Log error
                log_action(
                    action=action_template,
                    details={'error': str(e)},
                    status='error',
                    error=str(e)
                )
                raise
                
        return decorated_function
    return decorator

class AuditLogger:
    """Audit logging utility class"""
    
    @staticmethod
    def log_user_login(email, success=True):
        """Log user login attempt"""
        log_action(
            action='USER_LOGIN',
            details={'email': email},
            status='success' if success else 'error',
            error=None if success else 'Invalid credentials'
        )
    
    @staticmethod
    def log_user_registration(email, success=True):
        """Log user registration"""
        log_action(
            action='USER_REGISTER',
            details={'email': email},
            status='success' if success else 'error'
        )
    
    @staticmethod
    def log_startup_create(startup_id, business_name):
        """Log startup creation"""
        log_action(
            action='STARTUP_CREATE',
            details={'startup_id': startup_id, 'business_name': business_name},
            status='success'
        )
    
    @staticmethod
    def log_evaluation(startup_id, score):
        """Log evaluation"""
        log_action(
            action='EVALUATION_COMPLETE',
            details={'startup_id': startup_id, 'score': score},
            status='success'
        )
    
    @staticmethod
    def log_funding_request(startup_id, amount):
        """Log funding request"""
        log_action(
            action='FUNDING_REQUEST',
            details={'startup_id': startup_id, 'amount': amount},
            status='success'
        )
    
    @staticmethod
    def log_funding_approval(request_id, amount):
        """Log funding approval"""
        log_action(
            action='FUNDING_APPROVE',
            details={'request_id': request_id, 'amount': amount},
            status='success'
        )
    
    @staticmethod
    def log_funding_disbursement(request_id, amount):
        """Log funding disbursement"""
        log_action(
            action='FUNDING_DISBURSE',
            details={'request_id': request_id, 'amount': amount},
            status='success'
        )
    
    @staticmethod
    def log_grant_apply(grant_id, startup_id):
        """Log grant application"""
        log_action(
            action='GRANT_APPLY',
            details={'grant_id': grant_id, 'startup_id': startup_id},
            status='success'
        )
    
    @staticmethod
    def log_mentor_match(startup_id, mentor_ids):
        """Log mentor matching"""
        log_action(
            action='MENTOR_MATCH',
            details={'startup_id': startup_id, 'mentor_ids': mentor_ids},
            status='success'
        )
    
    @staticmethod
    def log_document_upload(document_id, filename):
        """Log document upload"""
        log_action(
            action='DOCUMENT_UPLOAD',
            details={'document_id': document_id, 'filename': filename},
            status='success'
        )
    
    @staticmethod
    def log_api_call(endpoint, method, status_code):
        """Log API call"""
        log_action(
            action='API_CALL',
            details={
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code
            },
            status='success' if status_code < 400 else 'error'
        )
    
    @staticmethod
    def get_audit_log(filters=None, limit=100, skip=0):
        """Retrieve audit logs with filters"""
        collection = get_collection(AUDIT_COLLECTION)
        
        query = {}
        if filters:
            if 'user_id' in filters:
                query['user_id'] = filters['user_id']
            if 'action' in filters:
                query['action'] = filters['action']
            if 'status' in filters:
                query['status'] = filters['status']
            if 'start_date' in filters:
                query['timestamp'] = {'$gte': filters['start_date']}
            if 'end_date' in filters:
                if 'timestamp' in query:
                    query['timestamp']['$lte'] = filters['end_date']
                else:
                    query['timestamp'] = {'$lte': filters['end_date']}
        
        logs = list(collection.find(query).sort('timestamp', -1).skip(skip).limit(limit))
        
        for log in logs:
            log['id'] = str(log['_id'])
            del log['_id']
            if log.get('user_id') is not None:
                log['user_id'] = str(log['user_id'])
        
        total = collection.count_documents(query)
        
        return {
            'logs': logs,
            'total': total,
            'limit': limit,
            'skip': skip
        }
    
    @staticmethod
    def get_user_audit(user_id, limit=50):
        """Get audit logs for a specific user"""
        return AuditLogger.get_audit_log(filters={'user_id': user_id}, limit=limit)
    
    @staticmethod
    def get_action_audit(action, limit=50):
        """Get audit logs for a specific action"""
        return AuditLogger.get_audit_log(filters={'action': action}, limit=limit)
    
    @staticmethod
    def get_audit_summary():
        """Get audit log summary"""
        collection = get_collection(AUDIT_COLLECTION)
        
        total = collection.count_documents({})
        actions = collection.distinct('action')
        users = collection.distinct('user_id')
        
        # Get counts by action
        action_counts = []
        for action in actions:
            count = collection.count_documents({'action': action})
            action_counts.append({'action': action, 'count': count})
        
        # Get recent activity (last 24 hours)
        from datetime import timedelta
        last_24h = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        recent = collection.count_documents({'timestamp': {'$gte': last_24h}})
        
        return {
            'total_logs': total,
            'unique_actions': len(actions),
            'unique_users': len(users),
            'recent_24h': recent,
            'action_counts': action_counts
        }
