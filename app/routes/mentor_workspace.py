"""Mentor workspace: a logged-in mentor sees, answers and replies to founders' requests."""
import json
import os
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_collection, USERS_COLLECTION
from app.utils.decorators import admin_required
from app.routes.sessions import get_sessions_data, save_sessions_data
from app.routes.messages import get_messages_data, save_messages_data, thread_key
from app.routes.mentors import get_mentors_data

mentor_workspace_bp = Blueprint('mentor_workspace', __name__)
LINK_FILE = './data/mentor_links.json'
NOT_LINKED = 'Your account is not linked to a mentor profile yet. Ask an admin.'


def _links():
    try:
        with open(LINK_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {'links': {}}


def _save_links(data):
    os.makedirs(os.path.dirname(LINK_FILE), exist_ok=True)
    with open(LINK_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def _my_mentor_id(user):
    linked = _links()['links'].get(str(user['_id']))
    if linked:
        return linked
    email = str(user.get('email') or '').lower()
    for m in get_mentors_data()['mentors']:
        if m.get('user_id') == user['_id']:
            return m['mentor_id']
        if email and str(m.get('email') or '').lower() == email:
            return m['mentor_id']
    return None


def _current_mentor():
    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': get_jwt_identity()})
    if not user or user.get('role') != 'mentor' or user.get('status') != 'active':
        return None, None, (jsonify({'error': 'An approved mentor account is required'}), 403)
    return user, _my_mentor_id(user), None


def _has_request(mentor_id, founder_id, accepted_only=False):
    for r in get_sessions_data()['requests']:
        if r.get('mentor_id') == mentor_id and r.get('user_id') == founder_id:
            if not accepted_only or r.get('status') == 'accepted':
                return True
    return False


@mentor_workspace_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user, mid, err = _current_mentor()
    if err:
        return err
    record = next((m for m in get_mentors_data()['mentors'] if m['mentor_id'] == mid), None)
    return jsonify({'success': True, 'linked': bool(mid), 'mentor': record,
                    'name': user.get('full_name')}), 200


@mentor_workspace_bp.route('/requests', methods=['GET'])
@jwt_required()
def my_requests():
    user, mid, err = _current_mentor()
    if err:
        return err
    if not mid:
        return jsonify({'success': True, 'linked': False, 'data': []}), 200
    users = get_collection(USERS_COLLECTION)
    out = []
    for r in get_sessions_data()['requests']:
        if r.get('mentor_id') != mid:
            continue
        founder = users.find_one({'_id': r['user_id']})
        out.append({**r, 'founder_name': founder.get('full_name', 'Founder') if founder else 'Founder'})
    out.sort(key=lambda r: r.get('created_at', ''), reverse=True)
    return jsonify({'success': True, 'linked': True, 'data': out}), 200


@mentor_workspace_bp.route('/requests/<request_id>/respond', methods=['POST'])
@jwt_required()
def respond(request_id):
    user, mid, err = _current_mentor()
    if err:
        return err
    if not mid:
        return jsonify({'error': NOT_LINKED}), 403
    body = request.get_json(silent=True) or {}
    action = body.get('action')
    if action not in ('accept', 'decline'):
        return jsonify({'error': "action must be 'accept' or 'decline'"}), 400
    data = get_sessions_data()
    for r in data['requests']:
        if r.get('request_id') != request_id:
            continue
        if r.get('mentor_id') != mid:
            return jsonify({'error': 'This request is not addressed to you'}), 403
        if r.get('status') != 'pending':
            return jsonify({'error': 'This request was already answered'}), 409
        r['status'] = 'accepted' if action == 'accept' else 'declined'
        r['mentor_note'] = (body.get('note') or '').strip()
        r['responded_at'] = datetime.utcnow().isoformat()
        save_sessions_data(data)
        try:
            from app.notifications import notify
            notify(r['user_id'], 'Mentor request ' + r['status'],
                   r['mentor_note'] or 'Your mentor answered your session request.')
        except Exception:
            pass
        return jsonify({'success': True, 'data': r}), 200
    return jsonify({'error': 'Request not found'}), 404


@mentor_workspace_bp.route('/thread/<founder_id>', methods=['GET'])
@jwt_required()
def get_thread(founder_id):
    user, mid, err = _current_mentor()
    if err:
        return err
    if not mid or not _has_request(mid, founder_id):
        return jsonify({'error': 'No request from this founder'}), 403
    thread = get_messages_data()['threads'].get(thread_key(founder_id, mid), [])
    shown = [{**m, 'from': 'founder' if m.get('from') == 'me' else m.get('from')} for m in thread]
    return jsonify({'success': True, 'data': shown}), 200


@mentor_workspace_bp.route('/thread/<founder_id>', methods=['POST'])
@jwt_required()
def reply(founder_id):
    user, mid, err = _current_mentor()
    if err:
        return err
    if not mid or not _has_request(mid, founder_id, accepted_only=True):
        return jsonify({'error': 'Accept the request before replying'}), 403
    text = ((request.get_json(silent=True) or {}).get('text') or '').strip()
    if not text:
        return jsonify({'error': 'Message text is required'}), 400
    messages = get_messages_data()
    thread = messages['threads'].setdefault(thread_key(founder_id, mid), [])
    msg = {'message_id': f'MSG-{len(thread) + 1:04d}', 'from': 'mentor', 'text': text,
           'created_at': datetime.utcnow().isoformat()}
    thread.append(msg)
    save_messages_data(messages)
    try:
        from app.notifications import notify
        notify(founder_id, 'New reply from your mentor', text[:120])
    except Exception:
        pass
    return jsonify({'success': True, 'data': msg}), 201


@mentor_workspace_bp.route('/link-options', methods=['GET'])
@admin_required
def link_options():
    users = get_collection(USERS_COLLECTION)
    mentor_users = [{'user_id': u['_id'], 'name': u.get('full_name'), 'email': u.get('email'),
                     'status': u.get('status')} for u in users.find({'role': 'mentor'})]
    records = [{'mentor_id': m['mentor_id'], 'name': m.get('full_name')}
               for m in get_mentors_data()['mentors']]
    return jsonify({'success': True, 'mentor_users': mentor_users,
                    'mentor_records': records, 'links': _links()['links']}), 200


@mentor_workspace_bp.route('/link', methods=['POST'])
@admin_required
def link():
    body = request.get_json(silent=True) or {}
    user_id, mentor_id = body.get('user_id'), body.get('mentor_id')
    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': user_id}) if user_id else None
    if not user or user.get('role') != 'mentor':
        return jsonify({'error': 'user_id must belong to a mentor account'}), 400
    if not any(m['mentor_id'] == mentor_id for m in get_mentors_data()['mentors']):
        return jsonify({'error': 'Unknown mentor_id'}), 400
    data = _links()
    data['links'][str(user_id)] = mentor_id
    _save_links(data)
    return jsonify({'success': True, 'links': data['links']}), 200
