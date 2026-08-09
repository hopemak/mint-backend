"""
Startup API - Complete startup management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.audit import log_action
import json
import os
from datetime import datetime
from app.database import get_collection, USERS_COLLECTION
from app.utils.decorators import admin_required

startups_bp = Blueprint('startups', __name__)

STARTUP_FILE = './data/startups.json'

def get_startups():
    try:
        with open(STARTUP_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'startups': []}

def save_startups(data):
    os.makedirs(os.path.dirname(STARTUP_FILE), exist_ok=True)
    with open(STARTUP_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@startups_bp.route('/', methods=['GET'])
@jwt_required()
def list_startups():
    data = get_startups()
    return jsonify({'success': True, 'data': data['startups']}), 200

@startups_bp.route('/<startup_id>', methods=['GET'])
@jwt_required()
def get_startup(startup_id):
    data = get_startups()
    for startup in data['startups']:
        if startup['startup_id'] == startup_id:
            return jsonify({'success': True, 'data': startup}), 200
    return jsonify({'error': 'Startup not found'}), 404

@startups_bp.route('/', methods=['POST'])
@jwt_required()
def create_startup():
    data = request.get_json()
    user_id = get_jwt_identity()
    required_fields = ['business_name', 'sector']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    startups_data = get_startups()
    new_startup = {
        'startup_id': f'MINT-2024-{len(startups_data["startups"]) + 1:04d}',
        'user_id': user_id,
        **data,
        'status': 'submitted',
        'created_at': datetime.utcnow().isoformat()
    }
    startups_data['startups'].append(new_startup)
    save_startups(startups_data)
    return jsonify({'success': True, 'data': new_startup}), 201

@startups_bp.route('/<startup_id>', methods=['PUT'])
@jwt_required()
def update_startup(startup_id):
    data = request.get_json()
    startups_data = get_startups()
    for i, startup in enumerate(startups_data['startups']):
        if startup['startup_id'] == startup_id:
            startups_data['startups'][i].update(data)
            startups_data['startups'][i]['updated_at'] = datetime.utcnow().isoformat()
            save_startups(startups_data)
            return jsonify({'success': True, 'data': startups_data['startups'][i]}), 200
    return jsonify({'error': 'Startup not found'}), 404

@startups_bp.route('/<startup_id>', methods=['DELETE'])
@jwt_required()
def delete_startup(startup_id):
    current_user_id = get_jwt_identity()
    startups_data = get_startups()

    target = None
    for startup in startups_data['startups']:
        if startup['startup_id'] == startup_id:
            target = startup
            break

    if not target:
        return jsonify({'error': 'Startup not found'}), 404

    is_owner = target.get('user_id') == current_user_id
    is_admin = False
    if not is_owner:
        users = get_collection(USERS_COLLECTION)
        caller = users.find_one({'_id': current_user_id})
        is_admin = bool(caller) and str(caller.get('role', '')).lower() == 'admin'

    if not is_owner and not is_admin:
        return jsonify({'error': 'Not authorized to delete this startup'}), 403

    startups_data['startups'] = [s for s in startups_data['startups'] if s['startup_id'] != startup_id]
    save_startups(startups_data)
    log_action('STARTUP_DELETE', details={'startup_id': startup_id}, status='success')
    return jsonify({'success': True, 'message': 'Startup deleted'}), 200

@startups_bp.route('/<startup_id>/status', methods=['PUT'])
@admin_required
def update_startup_status(startup_id):
    """Approve, reject, or otherwise change a startup's review status (admin only)"""
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400

    allowed_statuses = ['submitted', 'under_review', 'approved', 'rejected']
    new_status = data['status']
    if new_status not in allowed_statuses:
        return jsonify({'error': f'Status must be one of: {", ".join(allowed_statuses)}'}), 400

    startups_data = get_startups()
    for i, startup in enumerate(startups_data['startups']):
        if startup['startup_id'] == startup_id:
            startups_data['startups'][i]['status'] = new_status
            startups_data['startups'][i]['status_reason'] = data.get('reason', '')
            startups_data['startups'][i]['updated_at'] = datetime.utcnow().isoformat()
            save_startups(startups_data)
            log_action(
                'STARTUP_STATUS_UPDATE',
                details={'startup_id': startup_id, 'new_status': new_status, 'reason': data.get('reason', '')},
                status='success'
            )
            return jsonify({'success': True, 'message': 'Status updated', 'data': startups_data['startups'][i]}), 200
    return jsonify({'error': 'Startup not found'}), 404

@startups_bp.route('/my', methods=['GET'])
@jwt_required()
def get_my_startups():
    """Get current user's startups"""
    user_id = get_jwt_identity()
    startups_data = get_startups()
    my_startups = [s for s in startups_data['startups'] if s.get('user_id') == user_id]
    return jsonify({'success': True, 'data': my_startups}), 200

@startups_bp.route('/<startup_id>/team', methods=['GET'])
@jwt_required()
def get_startup_team(startup_id):
    """Get startup team members"""
    # In production, this would fetch from database
    return jsonify({
        'success': True,
        'data': {
            'members': [
                {'name': 'John Doe', 'role': 'Founder', 'joined': '2024-01-01'},
                {'name': 'Jane Smith', 'role': 'CTO', 'joined': '2024-01-15'}
            ]
        }
    }), 200

@startups_bp.route('/<startup_id>/team', methods=['POST'])
@jwt_required()
def add_team_member(startup_id):
    """Add team member to startup"""
    data = request.get_json()
    required_fields = ['name', 'role']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    return jsonify({
        'success': True,
        'message': 'Team member added successfully',
        'data': {
            'name': data['name'],
            'role': data['role'],
            'joined': datetime.utcnow().isoformat()
        }
    }), 201

@startups_bp.route('/<startup_id>/team/<member_id>', methods=['DELETE'])
@jwt_required()
def remove_team_member(startup_id, member_id):
    """Remove team member from startup"""
    return jsonify({
        'success': True,
        'message': 'Team member removed successfully'
    }), 200

@startups_bp.route('/sectors', methods=['GET'])
@jwt_required()
def list_sectors():
    """List all sectors"""
    sectors = [
        {'id': 'agriculture', 'name': 'Agriculture'},
        {'id': 'healthcare', 'name': 'Healthcare'},
        {'id': 'fintech', 'name': 'FinTech'},
        {'id': 'edtech', 'name': 'EdTech'},
        {'id': 'cleantech', 'name': 'CleanTech'},
        {'id': 'manufacturing', 'name': 'Manufacturing'},
        {'id': 'biotech', 'name': 'Biotech'},
        {'id': 'ai_ml', 'name': 'AI/ML'},
        {'id': 'logistics', 'name': 'Logistics'},
        {'id': 'energy', 'name': 'Energy'}
    ]
    return jsonify({'success': True, 'data': sectors}), 200
