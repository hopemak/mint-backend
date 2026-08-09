"""
Shared route decorators
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_collection, USERS_COLLECTION


def admin_required(fn):
    """Require the caller to be authenticated AND have role == 'admin' (case-insensitive)."""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        print(f"🔍 admin_required: JWT identity = {user_id!r} (type: {type(user_id).__name__})")

        users = get_collection(USERS_COLLECTION)
        user = users.find_one({'_id': user_id})
        print(f"🔍 admin_required: Mongo lookup for _id={user_id!r} -> found: {user is not None}")
        if user:
            print(f"🔍 admin_required: user.role = {user.get('role')!r}")

        if not user or str(user.get('role', '')).lower() != 'admin':
            print("🔍 admin_required: REJECTING (403)")
            return jsonify({'error': 'Admin access required'}), 403

        print("🔍 admin_required: ALLOWING")
        return fn(*args, **kwargs)
    return wrapper
