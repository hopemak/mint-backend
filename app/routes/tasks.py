"""
Task/Kanban Board API - Real project board tasks, MongoDB-backed
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid
import json
import os

from app.database import get_collection, USERS_COLLECTION
from app.audit import log_action

tasks_bp = Blueprint('tasks', __name__)

TASKS_COLLECTION = 'tasks'
STARTUP_FILE = './data/startups.json'  # startups.py is still JSON-backed; read-only lookup here

ALLOWED_COLUMNS = ['todo', 'progress', 'review', 'qa', 'done']
ALLOWED_PRIORITIES = ['High', 'Medium', 'Low']


def _get_startup(startup_id):
    try:
        with open(STARTUP_FILE, 'r') as f:
            data = json.load(f)
    except Exception:
        return None
    for s in data.get('startups', []):
        if s.get('startup_id') == startup_id:
            return s
    return None


def _is_admin(user_id):
    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': user_id})
    return bool(user) and str(user.get('role', '')).lower() == 'admin'


def _can_access_startup(user_id, startup_id):
    """Owner of the startup, or an admin, can manage its tasks."""
    startup = _get_startup(startup_id)
    if not startup:
        return False, 'Startup not found'
    if startup.get('user_id') == user_id:
        return True, None
    if _is_admin(user_id):
        return True, None
    return False, 'Not authorized for this startup'


def _serialize(task):
    out = dict(task)
    out['id'] = out.pop('_id', None)
    return out


@tasks_bp.route('/', methods=['GET'])
@jwt_required()
def list_tasks():
    startup_id = request.args.get('startup_id')
    if not startup_id:
        return jsonify({'error': 'startup_id query parameter is required'}), 400

    user_id = get_jwt_identity()
    allowed, err = _can_access_startup(user_id, startup_id)
    if not allowed:
        return jsonify({'error': err}), 403 if err != 'Startup not found' else 404

    collection = get_collection(TASKS_COLLECTION)
    tasks = [_serialize(t) for t in collection.find({'startup_id': startup_id})]
    return jsonify({'success': True, 'data': tasks}), 200


@tasks_bp.route('/', methods=['POST'])
@jwt_required()
def create_task():
    data = request.get_json() or {}
    user_id = get_jwt_identity()

    required_fields = ['title', 'startup_id']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing field: {field}'}), 400

    allowed, err = _can_access_startup(user_id, data['startup_id'])
    if not allowed:
        return jsonify({'error': err}), 403 if err != 'Startup not found' else 404

    column = data.get('column', 'todo')
    if column not in ALLOWED_COLUMNS:
        return jsonify({'error': f'column must be one of: {", ".join(ALLOWED_COLUMNS)}'}), 400

    priority = data.get('priority', 'Medium')
    if priority not in ALLOWED_PRIORITIES:
        return jsonify({'error': f'priority must be one of: {", ".join(ALLOWED_PRIORITIES)}'}), 400

    now = datetime.utcnow().isoformat()
    task = {
        '_id': str(uuid.uuid4()),
        'title': data['title'].strip(),
        'startup_id': data['startup_id'],
        'column': column,
        'priority': priority,
        'created_by': user_id,
        'created_at': now,
        'updated_at': now,
        'completed_at': now if column == 'done' else None,
    }

    collection = get_collection(TASKS_COLLECTION)
    collection.insert_one(task)

    log_action('TASK_CREATE', details={'task_id': task['_id'], 'startup_id': data['startup_id'], 'title': task['title']}, status='success')

    return jsonify({'success': True, 'data': _serialize(task)}), 201


@tasks_bp.route('/<task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    data = request.get_json() or {}
    user_id = get_jwt_identity()

    collection = get_collection(TASKS_COLLECTION)
    task = collection.find_one({'_id': task_id})
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    allowed, err = _can_access_startup(user_id, task['startup_id'])
    if not allowed:
        return jsonify({'error': err}), 403 if err != 'Startup not found' else 404

    update_fields = {}
    if 'title' in data:
        update_fields['title'] = data['title'].strip()
    if 'column' in data:
        if data['column'] not in ALLOWED_COLUMNS:
            return jsonify({'error': f'column must be one of: {", ".join(ALLOWED_COLUMNS)}'}), 400
        update_fields['column'] = data['column']
        update_fields['completed_at'] = datetime.utcnow().isoformat() if data['column'] == 'done' else None
    if 'priority' in data:
        if data['priority'] not in ALLOWED_PRIORITIES:
            return jsonify({'error': f'priority must be one of: {", ".join(ALLOWED_PRIORITIES)}'}), 400
        update_fields['priority'] = data['priority']

    update_fields['updated_at'] = datetime.utcnow().isoformat()
    collection.update_one({'_id': task_id}, {'$set': update_fields})

    updated = collection.find_one({'_id': task_id})
    log_action('TASK_UPDATE', details={'task_id': task_id, 'changes': update_fields}, status='success')

    return jsonify({'success': True, 'data': _serialize(updated)}), 200


@tasks_bp.route('/<task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()

    collection = get_collection(TASKS_COLLECTION)
    task = collection.find_one({'_id': task_id})
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    allowed, err = _can_access_startup(user_id, task['startup_id'])
    if not allowed:
        return jsonify({'error': err}), 403 if err != 'Startup not found' else 404

    collection.delete_one({'_id': task_id})
    log_action('TASK_DELETE', details={'task_id': task_id, 'startup_id': task['startup_id']}, status='success')

    return jsonify({'success': True, 'message': 'Task deleted'}), 200

@tasks_bp.route('/burndown', methods=['GET'])
@jwt_required()
def get_burndown():
    """Real burndown data derived from actual task completed_at timestamps."""
    startup_id = request.args.get('startup_id')
    if not startup_id:
        return jsonify({'error': 'startup_id query parameter is required'}), 400

    user_id = get_jwt_identity()
    allowed, err = _can_access_startup(user_id, startup_id)
    if not allowed:
        return jsonify({'error': err}), 403 if err != 'Startup not found' else 404

    days = int(request.args.get('days', 14))

    collection = get_collection(TASKS_COLLECTION)
    tasks = list(collection.find({'startup_id': startup_id}))

    if not tasks:
        return jsonify({'success': True, 'data': []}), 200

    from datetime import timedelta

    today = datetime.utcnow().date()
    start_day = today - timedelta(days=days - 1)

    total = len(tasks)
    result = []
    for i in range(days):
        day = start_day + timedelta(days=i)
        day_end = datetime.combine(day, datetime.max.time())

        existing = [t for t in tasks if datetime.fromisoformat(t['created_at']) <= day_end]
        remaining = [
            t for t in existing
            if not t.get('completed_at') or datetime.fromisoformat(t['completed_at']) > day_end
        ]

        ideal = max(0, round(total - (total / (days - 1)) * i)) if days > 1 else total

        result.append({
            'day': day.strftime('%b %d'),
            'ideal': ideal,
            'actual': len(remaining),
        })

    return jsonify({'success': True, 'data': result}), 200
