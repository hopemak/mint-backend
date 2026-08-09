"""
Audit Log Routes
Admin endpoints for viewing audit logs
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.audit import AuditLogger
from app.database import get_collection, USERS_COLLECTION

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    """Get audit logs (Admin only)"""
    user_id = get_jwt_identity()
    
    # Check if user is admin
    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': user_id})
    
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    # Get filters from query parameters
    filters = {}
    if request.args.get('user_id'):
        filters['user_id'] = request.args.get('user_id')
    if request.args.get('action'):
        filters['action'] = request.args.get('action')
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('start_date'):
        filters['start_date'] = request.args.get('start_date')
    if request.args.get('end_date'):
        filters['end_date'] = request.args.get('end_date')
    
    limit = int(request.args.get('limit', 100))
    skip = int(request.args.get('skip', 0))
    
    result = AuditLogger.get_audit_log(filters, limit, skip)
    
    return jsonify({
        'success': True,
        'data': result
    }), 200

@audit_bp.route('/logs/user/<user_id>', methods=['GET'])
@jwt_required()
def get_user_audit_logs(user_id):
    """Get audit logs for a specific user (Admin only)"""
    current_user_id = get_jwt_identity()
    
    # Check if user is admin
    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': current_user_id})
    
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    limit = int(request.args.get('limit', 50))
    result = AuditLogger.get_user_audit(user_id, limit)
    
    return jsonify({
        'success': True,
        'data': result
    }), 200

@audit_bp.route('/logs/action/<action>', methods=['GET'])
@jwt_required()
def get_action_audit_logs(action):
    """Get audit logs for a specific action (Admin only)"""
    current_user_id = get_jwt_identity()
    
    # Check if user is admin
    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': current_user_id})
    
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    limit = int(request.args.get('limit', 50))
    result = AuditLogger.get_action_audit(action, limit)
    
    return jsonify({
        'success': True,
        'data': result
    }), 200

@audit_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_audit_summary():
    """Get audit log summary (Admin only)"""
    current_user_id = get_jwt_identity()
    
    # Check if user is admin
    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': current_user_id})
    
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    summary = AuditLogger.get_audit_summary()
    
    return jsonify({
        'success': True,
        'data': summary
    }), 200

@audit_bp.route('/security-alerts', methods=['GET'])
@jwt_required()
def get_security_alerts():
    """Derive security alerts from the audit log (Admin only)"""
    current_user_id = get_jwt_identity()

    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': current_user_id})

    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    from datetime import datetime, timedelta
    from app.audit import AUDIT_COLLECTION

    collection = get_collection(AUDIT_COLLECTION)
    since = (datetime.utcnow() - timedelta(hours=24)).isoformat()

    alerts = []

    # Signal 1: repeated failed logins per email in the last 24h
    failed_logins = list(collection.find({
        'action': 'USER_LOGIN',
        'status': 'error',
        'timestamp': {'$gte': since}
    }))
    fail_counts = {}
    for entry in failed_logins:
        email = (entry.get('details') or {}).get('email', 'unknown')
        fail_counts[email] = fail_counts.get(email, 0) + 1

    for email, count in fail_counts.items():
        if count >= 3:
            alerts.append({
                'id': f'failed-login-{email}',
                'level': 'high' if count >= 5 else 'medium',
                'title': 'Repeated failed login attempts',
                'detail': f'{count} failed login attempts for {email} in the last 24h'
            })

    # Signal 2: any role escalation to admin in the last 24h
    role_changes = list(collection.find({
        'action': 'USER_ROLE_UPDATE',
        'timestamp': {'$gte': since}
    }))
    for entry in role_changes:
        details = entry.get('details') or {}
        if str(details.get('new_role', '')).lower() == 'admin':
            alerts.append({
                'id': f'role-escalation-{entry.get("_id")}',
                'level': 'medium',
                'title': 'User promoted to admin',
                'detail': f'User {details.get("target_user_id")} was promoted to admin'
            })

    return jsonify({'success': True, 'data': alerts}), 200
