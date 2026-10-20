"""
Mentor Session Requests API - Real tracked requests (no scheduling/video yet)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import os
from datetime import datetime

from app.database import get_collection, USERS_COLLECTION

sessions_bp = Blueprint('sessions', __name__)

SESSION_FILE = './data/sessions.json'

def get_sessions_data():
    try:
        with open(SESSION_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'requests': []}

def save_sessions_data(data):
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@sessions_bp.route('/mine', methods=['GET'])
@jwt_required()
def my_session_requests():
    user_id = get_jwt_identity()
    data = get_sessions_data()
    mine = [r for r in data['requests'] if r['user_id'] == user_id]
    return jsonify({'success': True, 'data': mine}), 200

@sessions_bp.route('/all', methods=['GET'])
@jwt_required()
def all_session_requests():
    """All session requests across all users, with requester name attached."""
    data = get_sessions_data()
    users = get_collection(USERS_COLLECTION)

    enriched = []
    for r in data['requests']:
        user = users.find_one({'_id': r['user_id']})
        enriched.append({
            **r,
            'user_name': user.get('full_name', 'Unknown user') if user else 'Unknown user',
        })

    return jsonify({'success': True, 'data': enriched}), 200

@sessions_bp.route('/<mentor_id>/request', methods=['POST'])
@jwt_required()
def request_session(mentor_id):
    user_id = get_jwt_identity()
    data = get_sessions_data()
    for r in data['requests']:
        if r['mentor_id'] == mentor_id and r['user_id'] == user_id and r['status'] == 'pending':
            return jsonify({'error': 'Already requested'}), 409
    new_request = {
        'request_id': f'SR-{len(data["requests"]) + 1:04d}',
        'user_id': user_id,
        'mentor_id': mentor_id,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat()
    }
    data['requests'].append(new_request)
    save_sessions_data(data)
    try:
        from app.notifications import notify_admins
        notify_admins('New mentor session request', 'A founder requested a mentor session.', '/admin')
    except Exception:
        pass
    return jsonify({'success': True, 'data': new_request}), 201
