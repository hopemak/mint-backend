"""
Admin Routes - Institution Codes & System Management
"""
from flask import Blueprint, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import get_collection
from datetime import datetime
import secrets

admin_bp = Blueprint('admin', __name__)
CORS(admin_bp, origins="*")

# In-memory fallbacks
_memory_codes = []
_memory_requests = []

@admin_bp.route('/codes', methods=['GET', 'OPTIONS'])
@jwt_required()
def list_institution_codes():
    codes_coll = get_collection('institution_codes')
    if codes_coll:
        codes = list(codes_coll.find({}, {'_id': 0}))
    else:
        codes = _memory_codes
    return jsonify({'success': True, 'codes': codes}), 200


@admin_bp.route('/codes', methods=['POST', 'OPTIONS'])
@jwt_required()
def create_institution_code():
    data = request.get_json() or {}
    prefix = data.get('prefix', 'MINT')
    count = min(data.get('count', 1), 50)

    codes_coll = get_collection('institution_codes')
    generated = []

    for _ in range(count):
        code = f"{prefix}-{secrets.token_hex(4).upper()}"
        doc = {
            'code': code,
            'used': False,
            'created_at': datetime.utcnow().isoformat()
        }
        if codes_coll:
            codes_coll.insert_one(doc)
        else:
            _memory_codes.append(doc)
        generated.append(code)

    return jsonify({
        'success': True,
        'codes': generated,
        'message': f'{len(generated)} code(s) generated'
    }), 201


# --- ACCESS REQUEST WORKFLOW ---

@admin_bp.route('/codes/requests', methods=['GET', 'OPTIONS'])
@jwt_required()
def list_requests():
    req_coll = get_collection('code_requests')
    if req_coll:
        requests = list(req_coll.find({}, {'_id': 0}).sort('created_at', -1))
    else:
        requests = sorted(_memory_requests, key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify({'success': True, 'requests': requests}), 200


@admin_bp.route('/codes/requests', methods=['POST', 'OPTIONS'])
def submit_request():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    role = data.get('role', '').strip()
    
    if not email or not role:
        return jsonify({'error': 'Email and role are required'}), 400

    doc = {
        'request_id': 'REQ-' + secrets.token_hex(4).upper(),
        'email': email,
        'role': role,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat()
    }

    req_coll = get_collection('code_requests')
    if req_coll:
        req_coll.insert_one(doc)
    else:
        _memory_requests.append(doc)

    return jsonify({
        'success': True,
        'message': 'Access request submitted. Admin will review shortly.',
        'request_id': doc['request_id']
    }), 201


@admin_bp.route('/codes/approve', methods=['POST', 'OPTIONS'])
@jwt_required()
def approve_request():
    data = request.get_json() or {}
    request_id = data.get('request_id', '').strip()
    
    if not request_id:
        return jsonify({'error': 'Request ID required'}), 400

    # Find the request
    req_coll = get_collection('code_requests')
    if req_coll:
        req_doc = req_coll.find_one({'request_id': request_id})
    else:
        req_doc = next((r for r in _memory_requests if r.get('request_id') == request_id), None)

    if not req_doc:
        return jsonify({'error': 'Request not found'}), 404

    if req_doc.get('status') == 'approved':
        return jsonify({'error': 'Already approved'}), 400

    # Generate code
    code = f"MINT-{secrets.token_hex(4).upper()}"
    
    # Save code
    codes_coll = get_collection('institution_codes')
    if codes_coll:
        codes_coll.insert_one({
            'code': code,
            'used': False,
            'created_at': datetime.utcnow().isoformat()
        })
    else:
        _memory_codes.append({
            'code': code,
            'used': False,
            'created_at': datetime.utcnow().isoformat()
        })

    # Update request status
    if req_coll:
        req_coll.update_one(
            {'request_id': request_id},
            {'$set': {'status': 'approved', 'code': code, 'approved_at': datetime.utcnow().isoformat()}}
        )
    else:
        for r in _memory_requests:
            if r.get('request_id') == request_id:
                r['status'] = 'approved'
                r['code'] = code
                r['approved_at'] = datetime.utcnow().isoformat()
                break

    # Try email
    emailed = False
    try:
        from app.email import EmailService
        svc = EmailService()
        if svc.enabled:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            sg = SendGridAPIClient(svc.api_key)
            message = Mail(
                from_email=svc.from_email,
                to_emails=req_doc['email'],
                subject='Your MInT Institution Access Code',
                html_content=f'<p>Your request has been approved!</p><p>Your institution code is: <strong>{code}</strong></p><p>Use this to register at MInT Innovation Platform.</p>'
            )
            sg.send(message)
            emailed = True
    except Exception as e:
        print('Email failed:', e)

    return jsonify({
        'success': True,
        'code': code,
        'email': req_doc['email'],
        'emailed': emailed,
        'message': 'Approved! Code sent via email.' if emailed else f'Approved! Code: {code} (email failed - copy manually)'
    }), 200
