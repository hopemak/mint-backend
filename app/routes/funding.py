"""
Funding API - MongoDB Version with Email Notifications
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid

from app.database import get_collection, USERS_COLLECTION, STARTUPS_COLLECTION
from app.email import send_funding_approved_email, send_funding_rejected_email

funding_bp = Blueprint('funding', __name__)

FUNDING_REQUESTS = 'funding_requests'
FUNDING_DISBURSEMENTS = 'funding_disbursements'

@funding_bp.route('/request', methods=['POST'])
@jwt_required()
def request_funding():
    """Request funding for a startup"""
    data = request.get_json()
    user_id = get_jwt_identity()
    
    required_fields = ['startup_id', 'amount', 'purpose', 'stage']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    collection = get_collection(FUNDING_REQUESTS)
    
    count = collection.count_documents({})
    request_id = f'FR-{str(count + 1).zfill(4)}'
    
    new_request = {
        '_id': str(uuid.uuid4()),
        'request_id': request_id,
        'startup_id': data['startup_id'],
        'user_id': user_id,
        'amount': data['amount'],
        'purpose': data['purpose'],
        'stage': data['stage'],
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    collection.insert_one(new_request)
    
    new_request['id'] = new_request['_id']
    del new_request['_id']
    
    return jsonify({
        'success': True,
        'message': 'Funding request submitted',
        'data': new_request
    }), 201

@funding_bp.route('/requests', methods=['GET'])
@jwt_required()
def get_funding_requests():
    """Get all funding requests"""
    collection = get_collection(FUNDING_REQUESTS)
    requests = list(collection.find())
    
    for req in requests:
        req['id'] = req['_id']
        del req['_id']
    
    return jsonify({'success': True, 'data': requests}), 200

@funding_bp.route('/requests/<request_id>', methods=['GET'])
@jwt_required()
def get_funding_request(request_id):
    """Get specific funding request"""
    collection = get_collection(FUNDING_REQUESTS)
    request = collection.find_one({'request_id': request_id})
    
    if not request:
        return jsonify({'error': 'Funding request not found'}), 404
    
    request['id'] = request['_id']
    del request['_id']
    
    return jsonify({'success': True, 'data': request}), 200

@funding_bp.route('/requests/<request_id>/approve', methods=['POST'])
@jwt_required()
def approve_funding(request_id):
    """Approve a funding request"""
    data = request.get_json()
    collection = get_collection(FUNDING_REQUESTS)
    
    request = collection.find_one({'request_id': request_id})
    if not request:
        return jsonify({'error': 'Funding request not found'}), 404
    
    approved_amount = data.get('approved_amount', request['amount'])
    
    collection.update_one(
        {'request_id': request_id},
        {'$set': {
            'status': 'approved',
            'approved_amount': approved_amount,
            'approved_by': get_jwt_identity(),
            'approved_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }}
    )
    
    # Send approval email
    try:
        startups = get_collection(STARTUPS_COLLECTION)
        startup = startups.find_one({'startup_id': request['startup_id']})
        
        users = get_collection(USERS_COLLECTION)
        user = users.find_one({'_id': request['user_id']})
        
        if user and startup:
            send_funding_approved_email(
                user['email'],
                user['full_name'],
                startup['business_name'],
                approved_amount,
                request_id
            )
            current_app.logger.info(f"✅ Funding approval email sent to {user['email']}")
    except Exception as e:
        current_app.logger.error(f"⚠️ Funding approval email failed: {e}")
    
    updated = collection.find_one({'request_id': request_id})
    updated['id'] = updated['_id']
    del updated['_id']
    
    return jsonify({
        'success': True,
        'message': 'Funding approved',
        'data': updated
    }), 200

@funding_bp.route('/requests/<request_id>/reject', methods=['POST'])
@jwt_required()
def reject_funding(request_id):
    """Reject a funding request"""
    data = request.get_json()
    collection = get_collection(FUNDING_REQUESTS)
    
    request = collection.find_one({'request_id': request_id})
    if not request:
        return jsonify({'error': 'Funding request not found'}), 404
    
    reason = data.get('reason', 'Not specified')
    
    collection.update_one(
        {'request_id': request_id},
        {'$set': {
            'status': 'rejected',
            'rejected_by': get_jwt_identity(),
            'rejected_at': datetime.utcnow().isoformat(),
            'rejection_reason': reason,
            'updated_at': datetime.utcnow().isoformat()
        }}
    )
    
    # Send rejection email
    try:
        startups = get_collection(STARTUPS_COLLECTION)
        startup = startups.find_one({'startup_id': request['startup_id']})
        
        users = get_collection(USERS_COLLECTION)
        user = users.find_one({'_id': request['user_id']})
        
        if user and startup:
            send_funding_rejected_email(
                user['email'],
                user['full_name'],
                startup['business_name'],
                reason
            )
            current_app.logger.info(f"✅ Funding rejection email sent to {user['email']}")
    except Exception as e:
        current_app.logger.error(f"⚠️ Funding rejection email failed: {e}")
    
    updated = collection.find_one({'request_id': request_id})
    updated['id'] = updated['_id']
    del updated['_id']
    
    return jsonify({
        'success': True,
        'message': 'Funding rejected',
        'data': updated
    }), 200

@funding_bp.route('/disburse', methods=['POST'])
@jwt_required()
def disburse_funding():
    """Disburse approved funding"""
    data = request.get_json()
    
    required_fields = ['request_id', 'amount', 'payment_method']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    requests_collection = get_collection(FUNDING_REQUESTS)
    disbursements_collection = get_collection(FUNDING_DISBURSEMENTS)
    
    request = requests_collection.find_one({'request_id': data['request_id']})
    if not request:
        return jsonify({'error': 'Funding request not found'}), 404
    
    if request['status'] != 'approved':
        return jsonify({'error': 'Funding not approved yet'}), 400
    
    count = disbursements_collection.count_documents({})
    disbursement_id = f'DS-{str(count + 1).zfill(4)}'
    
    disbursement = {
        '_id': str(uuid.uuid4()),
        'disbursement_id': disbursement_id,
        'request_id': data['request_id'],
        'amount': data['amount'],
        'payment_method': data['payment_method'],
        'payment_reference': data.get('payment_reference', ''),
        'disbursed_by': get_jwt_identity(),
        'disbursed_at': datetime.utcnow().isoformat(),
        'status': 'completed'
    }
    
    disbursements_collection.insert_one(disbursement)
    
    disbursement['id'] = disbursement['_id']
    del disbursement['_id']
    
    return jsonify({
        'success': True,
        'message': 'Funding disbursed successfully',
        'data': disbursement
    }), 201

@funding_bp.route('/disbursements', methods=['GET'])
@jwt_required()
def get_disbursements():
    """Get all disbursements"""
    collection = get_collection(FUNDING_DISBURSEMENTS)
    disbursements = list(collection.find())
    
    for d in disbursements:
        d['id'] = d['_id']
        del d['_id']
    
    return jsonify({'success': True, 'data': disbursements}), 200

@funding_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_funding_summary():
    """Get funding summary statistics"""
    requests_collection = get_collection(FUNDING_REQUESTS)
    disbursements_collection = get_collection(FUNDING_DISBURSEMENTS)
    
    all_requests = list(requests_collection.find())
    
    total_requested = sum(r.get('amount', 0) for r in all_requests)
    total_approved = sum(r.get('approved_amount', 0) for r in all_requests if r.get('status') == 'approved')
    pending = [r for r in all_requests if r.get('status') == 'pending']
    approved = [r for r in all_requests if r.get('status') == 'approved']
    rejected = [r for r in all_requests if r.get('status') == 'rejected']
    
    disbursements = list(disbursements_collection.find())
    total_disbursed = sum(d.get('amount', 0) for d in disbursements)
    
    return jsonify({
        'success': True,
        'data': {
            'total_requests': len(all_requests),
            'total_requested_amount': total_requested,
            'total_approved': len(approved),
            'total_approved_amount': total_approved,
            'total_disbursed_amount': total_disbursed,
            'pending_requests': len(pending),
            'rejected_requests': len(rejected)
        }
    }), 200
