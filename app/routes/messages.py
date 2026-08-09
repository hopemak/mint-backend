"""
Mentor Messages API - Persisted chat threads (founder <-> mentor)
No live mentor reply; this stores real messages tied to the user + mentor.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import os
from datetime import datetime

messages_bp = Blueprint('messages', __name__)

MESSAGE_FILE = './data/messages.json'

def get_messages_data():
    try:
        with open(MESSAGE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'threads': {}}

def save_messages_data(data):
    os.makedirs(os.path.dirname(MESSAGE_FILE), exist_ok=True)
    with open(MESSAGE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def thread_key(user_id, mentor_id):
    return f'{user_id}__{mentor_id}'

@messages_bp.route('/<mentor_id>', methods=['GET'])
@jwt_required()
def get_thread(mentor_id):
    user_id = get_jwt_identity()
    data = get_messages_data()
    key = thread_key(user_id, mentor_id)
    thread = data['threads'].get(key, [])
    return jsonify({'success': True, 'data': thread}), 200

@messages_bp.route('/<mentor_id>', methods=['POST'])
@jwt_required()
def send_message(mentor_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    text = (data or {}).get('text', '').strip()
    if not text:
        return jsonify({'error': 'Message text is required'}), 400

    messages_data = get_messages_data()
    key = thread_key(user_id, mentor_id)
    thread = messages_data['threads'].setdefault(key, [])
    new_message = {
        'message_id': f'MSG-{len(thread) + 1:04d}',
        'from': 'me',
        'text': text,
        'created_at': datetime.utcnow().isoformat()
    }
    thread.append(new_message)
    save_messages_data(messages_data)
    return jsonify({'success': True, 'data': new_message}), 201
