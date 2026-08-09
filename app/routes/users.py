"""
User Management API - Complete user management (MongoDB-backed)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.audit import log_action
from datetime import datetime

from app.database import get_collection, USERS_COLLECTION
from app.utils.decorators import admin_required

users_bp = Blueprint('users', __name__)


def _serialize_user(user_doc):
    """Convert a Mongo user document into the API-facing shape, stripping sensitive fields."""
    if not user_doc:
        return None
    out = dict(user_doc)
    out['id'] = out.pop('_id', None)
    out.pop('password', None)
    return out


def _is_admin(user_id):
    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': user_id})
    return bool(user) and str(user.get('role', '')).lower() == 'admin'


@users_bp.route('/', methods=['GET'])
@admin_required
def list_users():
    users = get_collection(USERS_COLLECTION)
    all_users = [_serialize_user(u) for u in users.find({})]
    return jsonify({'success': True, 'data': all_users}), 200


@users_bp.route('/<user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': user_id})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'success': True, 'data': _serialize_user(user)}), 200


@users_bp.route('/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    if current_user_id != user_id and not _is_admin(current_user_id):
        return jsonify({'error': 'Not authorized to edit this user'}), 403

    data = request.get_json() or {}
    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': user_id})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    allowed_fields = ['full_name', 'email', 'phone', 'bio', 'profile_image']
    update_fields = {f: data[f] for f in allowed_fields if f in data}
    update_fields['updated_at'] = datetime.utcnow().isoformat()

    users.update_one({'_id': user_id}, {'$set': update_fields})
    updated = users.find_one({'_id': user_id})
    return jsonify({'success': True, 'message': 'User updated', 'data': _serialize_user(updated)}), 200


@users_bp.route('/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    users = get_collection(USERS_COLLECTION)
    result = users.delete_one({'_id': user_id})
    if result.deleted_count == 0:
        return jsonify({'error': 'User not found'}), 404
    log_action('USER_DELETE', details={'target_user_id': user_id}, status='success')
    return jsonify({'success': True, 'message': 'User deleted'}), 200


@users_bp.route('/<user_id>/role', methods=['PUT'])
@admin_required
def update_user_role(user_id):
    data = request.get_json() or {}
    if 'role' not in data:
        return jsonify({'error': 'Role is required'}), 400

    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': user_id})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    users.update_one(
        {'_id': user_id},
        {'$set': {'role': data['role'], 'updated_at': datetime.utcnow().isoformat()}}
    )
    updated = users.find_one({'_id': user_id})
    log_action('USER_ROLE_UPDATE', details={'target_user_id': user_id, 'new_role': data['role']}, status='success')
    return jsonify({'success': True, 'message': 'Role updated', 'data': _serialize_user(updated)}), 200


@users_bp.route('/<user_id>/status', methods=['PUT'])
@admin_required
def update_user_status(user_id):
    data = request.get_json() or {}
    if 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400

    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': user_id})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    users.update_one(
        {'_id': user_id},
        {'$set': {'status': data['status'], 'updated_at': datetime.utcnow().isoformat()}}
    )
    updated = users.find_one({'_id': user_id})
    log_action('USER_STATUS_UPDATE', details={'target_user_id': user_id, 'new_status': data['status']}, status='success')
    return jsonify({'success': True, 'message': 'Status updated', 'data': _serialize_user(updated)}), 200


@users_bp.route('/<user_id>/permissions', methods=['GET'])
@jwt_required()
def get_user_permissions(user_id):
    # NOTE: still a static stub, not derived from the user's actual role yet.
    # Flagged as a known gap — left out of scope for this pass.
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
