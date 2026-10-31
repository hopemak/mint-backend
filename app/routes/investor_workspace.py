"""Investor workspace: browse approved ideas, keep a watchlist, show interest."""
import json
import os
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_collection, USERS_COLLECTION
from app.routes.ideas import load_ideas

investor_workspace_bp = Blueprint('investor_workspace', __name__)
FILE = './data/investor_activity.json'
PUBLIC = ('id', 'title', 'problem', 'solution', 'category', 'industry',
          'innovation_level', 'created_at')


def _load():
    try:
        with open(FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {'watch': {}, 'interests': []}


def _save(data):
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, 'w') as f:
        json.dump(data, f, indent=2)


def _investor():
    user = get_collection(USERS_COLLECTION).find_one({'_id': get_jwt_identity()})
    if not user or user.get('role') != 'investor' or user.get('status') != 'active':
        return None, (jsonify({'error': 'An approved investor account is required'}), 403)
    return user, None


def _approved():
    ideas = load_ideas()
    ideas = ideas.get('ideas', []) if isinstance(ideas, dict) else ideas
    return [i for i in ideas if isinstance(i, dict) and i.get('status') == 'approved']


def _owner_id(idea):
    for key in ('owner_id', 'user_id', 'created_by', 'founder_id'):
        if idea.get(key):
            return idea[key]
    return None


@investor_workspace_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user, err = _investor()
    if err:
        return err
    return jsonify({'success': True, 'name': user.get('full_name'),
                    'firm_name': user.get('firm_name', ''), 'focus': user.get('focus', ''),
                    'investment_stage': user.get('investment_stage', '')}), 200


@investor_workspace_bp.route('/startups', methods=['GET'])
@jwt_required()
def startups():
    user, err = _investor()
    if err:
        return err
    q = (request.args.get('q') or '').strip().lower()
    industry = (request.args.get('industry') or '').strip()
    activity = _load()
    uid = str(user['_id'])
    watched = set(activity['watch'].get(uid, []))
    interested = {i['idea_id'] for i in activity['interests'] if i['investor_id'] == uid}
    out = []
    for idea in _approved():
        text = ' '.join(str(idea.get(k) or '') for k in ('title', 'problem', 'solution')).lower()
        if q and q not in text:
            continue
        if industry and idea.get('industry') != industry:
            continue
        row = {k: idea.get(k) for k in PUBLIC}
        row['watched'] = idea.get('id') in watched
        row['interested'] = idea.get('id') in interested
        out.append(row)
    out.sort(key=lambda r: r.get('created_at') or '', reverse=True)
    return jsonify({'success': True, 'data': out}), 200


@investor_workspace_bp.route('/watch/<idea_id>', methods=['POST'])
@jwt_required()
def watch(idea_id):
    user, err = _investor()
    if err:
        return err
    if not any(i.get('id') == idea_id for i in _approved()):
        return jsonify({'error': 'Idea not found'}), 404
    activity = _load()
    uid = str(user['_id'])
    items = activity['watch'].setdefault(uid, [])
    if idea_id in items:
        items.remove(idea_id)
        watched = False
    else:
        items.append(idea_id)
        watched = True
    _save(activity)
    return jsonify({'success': True, 'watched': watched}), 200


@investor_workspace_bp.route('/interest/<idea_id>', methods=['POST'])
@jwt_required()
def interest(idea_id):
    user, err = _investor()
    if err:
        return err
    idea = next((i for i in _approved() if i.get('id') == idea_id), None)
    if not idea:
        return jsonify({'error': 'Idea not found'}), 404
    note = ((request.get_json(silent=True) or {}).get('note') or '').strip()
    if len(note) < 10:
        return jsonify({'error': 'Add a short message (at least 10 characters)'}), 400
    activity = _load()
    uid = str(user['_id'])
    if any(i['investor_id'] == uid and i['idea_id'] == idea_id for i in activity['interests']):
        return jsonify({'error': 'You already showed interest in this idea'}), 409
    activity['interests'].append({
        'investor_id': uid, 'idea_id': idea_id, 'note': note,
        'created_at': datetime.utcnow().isoformat(),
    })
    _save(activity)
    who = user.get('firm_name') or user.get('full_name') or 'An investor'
    try:
        from app.notifications import notify, notify_admins
        owner = _owner_id(idea)
        if owner:
            notify(owner, 'An investor is interested in your idea',
                   who + ' on "' + str(idea.get('title')) + '": ' + note[:160])
        notify_admins('Investor interest', who + ' showed interest in "' + str(idea.get('title')) + '".')
    except Exception:
        pass
    return jsonify({'success': True}), 201
