"""
User Management API - Complete user management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import os
from datetime import datetime
import bcrypt

users_bp = Blueprint('users', __name__)

USER_FILE = './data/users.json'

def get_users():
    try:
        with open(USER_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'users': []}

def save_users(data):
    os.makedirs(os.path.dirname(USER_FILE), exist_ok=True)
    with open(USER_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@users_bp.route('/', methods=['GET'])
@jwt_required()
def list_users():
    users = get_users()
    return jsonify({'success': True, 'data': users['users']}), 200

@users_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    users = get_users()
    for user in users['users']:
        if user['id'] == user_id:
            user_copy = user.copy()
            user_copy.pop('password', None)
            return jsonify({'success': True, 'data': user_copy}), 200
    return jsonify({'error': 'User not found'}), 404

@users_bp.route('/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    users = get_users()
    
    for i, user in enumerate(users['users']):
        if user['id'] == user_id:
            allowed_fields = ['full_name', 'email', 'phone', 'bio', 'profile_image']
            for field in allowed_fields:
                if field in data:
                    users['users'][i][field] = data[field]
            users['users'][i]['updated_at'] = datetime.utcnow().isoformat()
            save_users(users)
            return jsonify({'success': True, 'message': 'User updated', 'data': users['users'][i]}), 200
    return jsonify({'error': 'User not found'}), 404

@users_bp.route('/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    users = get_users()
    for i, user in enumerate(users['users']):
        if user['id'] == user_id:
            users['users'].pop(i)
            save_users(users)
            return jsonify({'success': True, 'message': 'User deleted'}), 200
    return jsonify({'error': 'User not found'}), 404

@users_bp.route('/<user_id>/role', methods=['PUT'])
@jwt_required()
def update_user_role(user_id):
    data = request.get_json()
    if 'role' not in data:
        return jsonify({'error': 'Role is required'}), 400
    users = get_users()
    for i, user in enumerate(users['users']):
        if user['id'] == user_id:
            users['users'][i]['role'] = data['role']
            users['users'][i]['updated_at'] = datetime.utcnow().isoformat()
            save_users(users)
            return jsonify({'success': True, 'message': 'Role updated', 'data': users['users'][i]}), 200
    return jsonify({'error': 'User not found'}), 404

@users_bp.route('/<user_id>/status', methods=['PUT'])
@jwt_required()
def update_user_status(user_id):
    data = request.get_json()
    if 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
    users = get_users()
    for i, user in enumerate(users['users']):
        if user['id'] == user_id:
            users['users'][i]['status'] = data['status']
            users['users'][i]['updated_at'] = datetime.utcnow().isoformat()
            save_users(users)
            return jsonify({'success': True, 'message': 'Status updated', 'data': users['users'][i]}), 200
    return jsonify({'error': 'User not found'}), 404

@users_bp.route('/<user_id>/permissions', methods=['GET'])
@jwt_required()
def get_user_permissions(user_id):
    permissions = {
        'can_create_startup': True,
        'can_evaluate_startup': False,
        'can_approve_funding': False,
        'can_manage_users': False,
        'can_view_all': False
    }
    return jsonify({'success': True, 'data': permissions}), 200

@users_bp.route('/roles', methods=['GET'])
@jwt_required()
def list_roles():
    roles = [
        {'id': 'admin', 'name': 'Administrator', 'description': 'Full system access'},
        {'id': 'founder', 'name': 'Startup Founder', 'description': 'Startup management'},
        {'id': 'mentor', 'name': 'Mentor', 'description': 'Startup mentoring'},
        {'id': 'investor', 'name': 'Investor', 'description': 'Investment management'},
        {'id': 'committee', 'name': 'Committee Member', 'description': 'Evaluation committee'},
        {'id': 'viewer', 'name': 'Viewer', 'description': 'Read-only access'}
    ]
    return jsonify({'success': True, 'data': roles}), 200
