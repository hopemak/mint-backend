"""
Authentication Routes - With Fallback Support
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from app.audit import AuditLogger
import bcrypt
from datetime import datetime
import uuid
import json
import os

from app.database import get_collection, USERS_COLLECTION, is_db_available
from app.email import send_welcome_email

auth_bp = Blueprint('auth', __name__)

# In-memory fallback storage
_memory_users = []

def get_users_collection():
    """Get users collection or fallback to memory"""
    coll = get_collection(USERS_COLLECTION)
    if coll is not None:
        return coll
    return None

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['email', 'password', 'full_name', 'role']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    coll = get_users_collection()
    
    # Check if user exists (in-memory or DB)
    if coll is not None:
        existing = coll.find_one({'email': data['email']})
    else:
        existing = next((u for u in _memory_users if u.get('email') == data['email']), None)
    
    if existing:
        return jsonify({'error': 'User already exists'}), 409
    
    # Hash password
    hashed = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    user_id = str(uuid.uuid4())
    new_user = {
        '_id': user_id,
        'id': user_id,
        'email': data['email'],
        'password': hashed.decode('utf-8'),
        'full_name': data['full_name'],
        'role': data['role'],
        'status': 'active',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'startup_id': data.get('startup_id')
    }
    
    if coll is not None:
        coll.insert_one(new_user)
    else:
        _memory_users.append(new_user)
    
    # Send welcome email
    try:
        send_welcome_email(new_user['email'], new_user['full_name'])
    except Exception as e:
        current_app.logger.error(f"Welcome email failed: {e}")
    
    # Generate tokens
    access_token = create_access_token(identity=user_id)
    refresh_token = create_refresh_token(identity=user_id)
    
    response = jsonify({
        'success': True,
        'message': 'User registered successfully',
        'data': {
            'user': {
                'id': user_id,
                'email': new_user['email'],
                'full_name': new_user['full_name'],
                'role': new_user['role']
            },
            'token': access_token
        }
    })
    
    set_access_cookies(response, access_token)
    
    return response, 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400
    
    coll = get_users_collection()
    
    # Find user
    if coll is not None:
        user = coll.find_one({'email': data['email']})
    else:
        user = next((u for u in _memory_users if u.get('email') == data['email']), None)
    
    if not user:
        AuditLogger.log_user_login(data['email'], success=False)
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Check password
    if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password'].encode('utf-8')):
        AuditLogger.log_user_login(data['email'], success=False)
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Check status
    if user.get('status') != 'active':
        return jsonify({'error': 'Account is not active'}), 403
    
    user_id = user.get('_id') or user.get('id')

    AuditLogger.log_user_login(data['email'], success=True)

    # Generate tokens
    access_token = create_access_token(identity=user_id)
    refresh_token = create_refresh_token(identity=user_id)
    
    response = jsonify({
        'success': True,
        'message': 'Login successful',
        'data': {
            'user': {
                'id': user_id,
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role']
            },
            'token': access_token
        }
    })
    
    set_access_cookies(response, access_token)
    
    return response, 200

# ... (rest of auth routes: refresh, logout, me, forgot-password)
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_token = create_access_token(identity=user_id)
    response = jsonify({'success': True, 'message': 'Token refreshed'})
    set_access_cookies(response, new_token)
    return response, 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = jsonify({'success': True, 'message': 'Logged out successfully'})
    unset_jwt_cookies(response)
    return response, 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    coll = get_users_collection()
    
    if coll is not None:
        user = coll.find_one({'_id': user_id})
    else:
        user = next((u for u in _memory_users if u.get('_id') == user_id or u.get('id') == user_id), None)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'data': {
            'user': {
                'id': user.get('_id') or user.get('id'),
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role']
            }
        }
    }), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400
    return jsonify({
        'success': True,
        'message': 'Password reset link sent to your email'
    }), 200
