"""Self-service profile, password and notification endpoints."""
import bcrypt
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import get_collection, USERS_COLLECTION

account_bp = Blueprint('account', __name__, url_prefix='/api/account')
notif_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

EDITABLE = {'full_name': 80, 'phone': 30, 'bio': 500, 'organization': 120, 'region': 60}


def _me():
    users = get_collection(USERS_COLLECTION)
    return users.find_one({'_id': get_jwt_identity()}) if users is not None else None


def _out(u):
    return {'id': u['_id'], 'email': u.get('email'), 'full_name': u.get('full_name', ''),
            'role': u.get('role'), 'status': u.get('status'), 'phone': u.get('phone', ''),
            'bio': u.get('bio', ''), 'organization': u.get('organization', ''),
            'region': u.get('region', ''), 'expertise': u.get('expertise') or [],
            'email_verified': u.get('email_verified'), 'created_at': u.get('created_at', '')}


def _summary(u):
    out = {'startups': 0, 'funding_requests': 0, 'funding_approved': 0, 'testimonials': 0}
    try:
        from app.routes.startups import get_startups
        out['startups'] = sum(1 for s in (get_startups() or {}).get('startups', [])
                              if s.get('user_id') == u['_id'])
    except Exception:
        pass
    try:
        from app.routes.funding import FUNDING_REQUESTS
        fc = get_collection(FUNDING_REQUESTS)
        if fc is not None:
            rows = list(fc.find({'user_id': u['_id']}))
            out['funding_requests'] = len(rows)
            out['funding_approved'] = sum(float(r.get('approved_amount') or 0)
                                          for r in rows if r.get('status') == 'approved')
    except Exception:
        pass
    try:
        tc = get_collection('testimonials')
        if tc is not None:
            out['testimonials'] = tc.count_documents({'user_id': u['_id']})
    except Exception:
        pass
    return out


@account_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    u = _me()
    if not u:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': _out(u), 'summary': _summary(u)}), 200


@account_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_me():
    u = _me()
    if not u:
        return jsonify({'error': 'User not found'}), 404
    data = request.get_json() or {}
    changes = {}
    for k, limit in EDITABLE.items():
        if k in data:
            changes[k] = str(data[k]).strip()[:limit]
    if 'full_name' in changes and len(changes['full_name']) < 2:
        return jsonify({'error': 'Name is too short'}), 400
    if 'expertise' in data and isinstance(data['expertise'], list):
        changes['expertise'] = [str(x).strip()[:40] for x in data['expertise'] if str(x).strip()][:12]
    if not changes:
        return jsonify({'error': 'Nothing to update'}), 400
    changes['updated_at'] = datetime.utcnow().isoformat()
    get_collection(USERS_COLLECTION).update_one({'_id': u['_id']}, {'$set': changes})
    return jsonify({'user': _out(_me())}), 200


@account_bp.route('/password', methods=['PUT'])
@jwt_required()
def change_password():
    u = _me()
    if not u:
        return jsonify({'error': 'User not found'}), 404
    data = request.get_json() or {}
    cur, new = str(data.get('current_password', '')), str(data.get('new_password', ''))
    if len(new) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400
    if new == cur:
        return jsonify({'error': 'New password must be different'}), 400
    if not bcrypt.checkpw(cur.encode('utf-8'), str(u.get('password', '')).encode('utf-8')):
        return jsonify({'error': 'Current password is incorrect'}), 403
    hashed = bcrypt.hashpw(new.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    get_collection(USERS_COLLECTION).update_one(
        {'_id': u['_id']}, {'$set': {'password': hashed, 'updated_at': datetime.utcnow().isoformat()}})
    return jsonify({'success': True}), 200


# ---------------- notifications ----------------
@notif_bp.route('', methods=['GET'])
@jwt_required()
def list_notifications():
    coll = get_collection('notifications')
    if coll is None:
        return jsonify({'notifications': [], 'unread': 0}), 200
    uid = get_jwt_identity()
    docs = coll.find({'user_id': uid}).sort('created_at', -1).limit(20)
    return jsonify({
        'notifications': [{'id': d['_id'], 'title': d.get('title', ''), 'message': d.get('message', ''),
                           'link': d.get('link'), 'read': bool(d.get('read')),
                           'created_at': d.get('created_at', '')} for d in docs],
        'unread': coll.count_documents({'user_id': uid, 'read': False}),
    }), 200


@notif_bp.route('/<nid>/read', methods=['PUT'])
@jwt_required()
def mark_read(nid):
    coll = get_collection('notifications')
    if coll is not None:
        coll.update_one({'_id': nid, 'user_id': get_jwt_identity()}, {'$set': {'read': True}})
    return jsonify({'success': True}), 200


@notif_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_read():
    coll = get_collection('notifications')
    if coll is not None:
        coll.update_many({'user_id': get_jwt_identity(), 'read': False}, {'$set': {'read': True}})
    return jsonify({'success': True}), 200
