"""Startup milestones stored in MongoDB (owner or admin only)."""
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import get_collection, USERS_COLLECTION

milestones_bp = Blueprint('milestones', __name__, url_prefix='/api/milestones')


def _user():
    users = get_collection(USERS_COLLECTION)
    return users.find_one({'_id': get_jwt_identity()}) if users is not None else None


def _out(d):
    return {'id': d['_id'], 'startup_id': d.get('startup_id'), 'title': d.get('title', ''),
            'date': d.get('date', ''), 'completed': bool(d.get('completed'))}


def _own(coll, mid, user):
    doc = coll.find_one({'_id': mid})
    if not doc or (doc.get('user_id') != user['_id'] and user.get('role') != 'admin'):
        return None
    return doc


@milestones_bp.route('', methods=['GET'])
@jwt_required()
def list_milestones():
    user, coll = _user(), get_collection('milestones')
    if not user or coll is None:
        return jsonify({'milestones': []}), 200
    q = {'startup_id': request.args.get('startup_id', '')}
    if user.get('role') != 'admin':
        q['user_id'] = user['_id']
    return jsonify({'milestones': [_out(d) for d in coll.find(q).sort('date', 1)]}), 200


@milestones_bp.route('', methods=['POST'])
@jwt_required()
def create_milestone():
    user, coll = _user(), get_collection('milestones')
    data = request.get_json() or {}
    title, date, sid = str(data.get('title', '')).strip(), str(data.get('date', '')).strip(), data.get('startup_id')
    if not user or coll is None:
        return jsonify({'error': 'Unavailable'}), 503
    if not title or not date or not sid:
        return jsonify({'error': 'title, date and startup_id are required'}), 400
    doc = {'_id': str(uuid.uuid4()), 'user_id': user['_id'], 'startup_id': sid,
           'title': title[:200], 'date': date, 'completed': False,
           'created_at': datetime.utcnow().isoformat()}
    coll.insert_one(doc)
    return jsonify({'milestone': _out(doc)}), 201


@milestones_bp.route('/<mid>', methods=['PUT'])
@jwt_required()
def update_milestone(mid):
    user, coll = _user(), get_collection('milestones')
    if not user or coll is None or not _own(coll, mid, user):
        return jsonify({'error': 'Not found'}), 404
    coll.update_one({'_id': mid}, {'$set': {'completed': bool((request.get_json() or {}).get('completed'))}})
    return jsonify({'success': True}), 200


@milestones_bp.route('/<mid>', methods=['DELETE'])
@jwt_required()
def delete_milestone(mid):
    user, coll = _user(), get_collection('milestones')
    if not user or coll is None or not _own(coll, mid, user):
        return jsonify({'error': 'Not found'}), 404
    coll.delete_one({'_id': mid})
    return jsonify({'success': True}), 200
