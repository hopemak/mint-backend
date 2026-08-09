"""
Startup Events API - Listing and real registration tracking
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.audit import log_action
from app.utils.decorators import admin_required
import json
import os
from datetime import datetime

events_bp = Blueprint('events', __name__)

EVENT_FILE = './data/events.json'

def get_events_data():
    try:
        with open(EVENT_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'events': []}

def save_events_data(data):
    os.makedirs(os.path.dirname(EVENT_FILE), exist_ok=True)
    with open(EVENT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@events_bp.route('/', methods=['GET'])
@jwt_required()
def list_events():
    user_id = get_jwt_identity()
    data = get_events_data()
    events = []
    for e in data['events']:
        e_copy = dict(e)
        e_copy['registered'] = user_id in e.get('registered_users', [])
        e_copy.pop('registered_users', None)
        events.append(e_copy)
    return jsonify({'success': True, 'data': events}), 200

@events_bp.route('/<event_id>', methods=['GET'])
@jwt_required()
def get_event(event_id):
    user_id = get_jwt_identity()
    data = get_events_data()
    for e in data['events']:
        if e['event_id'] == event_id:
            e_copy = dict(e)
            e_copy['registered'] = user_id in e.get('registered_users', [])
            e_copy.pop('registered_users', None)
            return jsonify({'success': True, 'data': e_copy}), 200
    return jsonify({'error': 'Event not found'}), 404

@events_bp.route('/', methods=['POST'])
@admin_required
def create_event():
    data = request.get_json()
    required_fields = ['title', 'day', 'month', 'year', 'location', 'time']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    events_data = get_events_data()
    new_event = {
        'event_id': f'E-{len(events_data["events"]) + 1:04d}',
        **data,
        'registered_users': [],
        'created_at': datetime.utcnow().isoformat()
    }
    events_data['events'].append(new_event)
    save_events_data(events_data)
    log_action('EVENT_CREATE', details={'title': new_event.get('title')}, status='success')
    return jsonify({'success': True, 'data': new_event}), 201

@events_bp.route('/<event_id>/register', methods=['POST'])
@jwt_required()
def register_for_event(event_id):
    user_id = get_jwt_identity()
    events_data = get_events_data()
    for e in events_data['events']:
        if e['event_id'] == event_id:
            registered_users = e.setdefault('registered_users', [])
            if user_id in registered_users:
                return jsonify({'error': 'Already registered'}), 409
            registered_users.append(user_id)
            save_events_data(events_data)
            return jsonify({'success': True, 'message': 'Registered', 'data': {'registered': True}}), 200
    return jsonify({'error': 'Event not found'}), 404

@events_bp.route('/<event_id>/register', methods=['DELETE'])
@jwt_required()
def unregister_from_event(event_id):
    user_id = get_jwt_identity()
    events_data = get_events_data()
    for e in events_data['events']:
        if e['event_id'] == event_id:
            registered_users = e.setdefault('registered_users', [])
            if user_id in registered_users:
                registered_users.remove(user_id)
                save_events_data(events_data)
            return jsonify({'success': True, 'message': 'Unregistered', 'data': {'registered': False}}), 200
    return jsonify({'error': 'Event not found'}), 404
