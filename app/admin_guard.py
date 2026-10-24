"""Admin-only check. The role is read from the database, never from the browser."""
from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.database import get_collection


def _find_user(user_id):
    users = get_collection('users')
    if users is None:
        raise RuntimeError('database unavailable')
    user = None
    try:
        from bson import ObjectId
        user = users.find_one({'_id': ObjectId(user_id)})
    except Exception:
        user = None
    if user is None:
        user = users.find_one({'$or': [{'id': user_id}, {'_id': user_id}]})
    return user


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({'error': 'Authentication required'}), 401
        try:
            user = _find_user(str(get_jwt_identity()))
        except Exception:
            return jsonify({'error': 'Could not verify permissions'}), 503
        if not user or user.get('role') != 'admin' or user.get('status') == 'inactive':
            return jsonify({'error': 'Admin access required'}), 403
        g.admin_user = user
        return fn(*args, **kwargs)
    return wrapper
