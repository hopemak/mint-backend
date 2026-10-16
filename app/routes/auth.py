"""
Authentication Routes - With Fallback Support
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from app.audit import AuditLogger
import bcrypt
from datetime import datetime
import uuid
import json
import os
import secrets
from datetime import timedelta

from app.database import get_collection, USERS_COLLECTION, is_db_available
from app.email import send_welcome_email, send_login_otp_email, email_service

auth_bp = Blueprint('auth', __name__)

# In-memory fallback storage
_memory_users = []
_memory_otps = []
_memory_codes = []

def get_users_collection():
    """Get users collection or fallback to memory"""
    coll = get_collection(USERS_COLLECTION)
    if coll is not None:
        return coll
    return None

def _discard_unverified_user(user, email):
    users_coll = get_users_collection()
    otp_coll = get_collection('auth_otps')
    codes_coll = get_collection('institution_codes')
    code = user.get('institution_code')
    if users_coll is not None:
        users_coll.delete_one({'email': email, 'email_verified': False})
    else:
        _memory_users[:] = [u for u in _memory_users if u.get('email') != email]
    if otp_coll is not None:
        otp_coll.delete_many({'email': email, 'purpose': 'registration'})
    else:
        _memory_otps[:] = [o for o in _memory_otps if not (o.get('email') == email and o.get('purpose') == 'registration')]
    if code:
        if codes_coll is not None:
            codes_coll.delete_one({'code': code})
        else:
            _memory_codes[:] = [c for c in _memory_codes if c.get('code') != code]


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register an account, generate its institution code, and verify email."""
    data = request.get_json() or {}

    for field in ('email', 'password', 'full_name', 'role'):
        if not data.get(field):
            return jsonify({'error': f'Missing field: {field}'}), 400

    email = str(data['email']).strip().lower()
    role = str(data['role']).strip().lower()
    full_name = str(data['full_name']).strip()

    if not full_name or '@' not in email:
        return jsonify({'error': 'Enter a valid name and email address.'}), 400

    if role not in ('founder', 'mentor', 'investor'):
        return jsonify({
            'error': 'Invalid role. Must be one of: founder, mentor, investor'
        }), 400

    if not email_service.enabled:
        return jsonify({
            'error': 'Email delivery is not configured. Please contact the administrator.'
        }), 503

    coll = get_users_collection()
    existing = (
        coll.find_one({'email': email}) if coll is not None
        else next((u for u in _memory_users if u.get('email') == email), None)
    )
    if existing:
        if existing.get('email_verified') is False:
            _discard_unverified_user(existing, email)
        else:
            return jsonify({'error': 'User already exists'}), 409

    codes_coll = get_collection('institution_codes')
    institution_code = None

    # Generate a unique code using the same format as the admin code system.
    for _ in range(10):
        candidate = f"MINT-{secrets.token_hex(4).upper()}"
        exists = (
            codes_coll.find_one({'code': candidate}) if codes_coll is not None
            else any(c.get('code') == candidate for c in _memory_codes)
        )
        if not exists:
            institution_code = candidate
            break

    if not institution_code:
        return jsonify({'error': 'Could not generate an institution code. Please retry.'}), 500

    now = datetime.utcnow()
    user_id = str(uuid.uuid4())
    account_status = 'active' if role == 'founder' else 'pending'

    new_user = {
        '_id': user_id,
        'id': user_id,
        'email': email,
        'password': bcrypt.hashpw(
            data['password'].encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8'),
        'full_name': full_name,
        'role': role,
        'status': account_status,
        'email_verified': False,
        'created_at': now.isoformat(),
        'updated_at': now.isoformat(),
        'startup_id': data.get('startup_id'),
        'institution_code': institution_code
    }

    if role in ('mentor', 'founder'):
        new_user['expertise_areas'] = data.get('expertise_areas', '')
        new_user['years_experience'] = data.get('years_experience', 0)
    elif role == 'investor':
        new_user['firm_name'] = data.get('firm_name', '')
        new_user['focus'] = data.get('focus', '')
        new_user['investment_stage'] = data.get('investment_stage', '')

    code_doc = {
        'code': institution_code,
        'used': False,
        'created_at': now.isoformat(),
        'user_id': user_id
    }

    otp = f"{secrets.randbelow(1000000):06d}"
    otp_hash = bcrypt.hashpw(
        otp.encode('utf-8'), bcrypt.gensalt()
    ).decode('utf-8')
    otp_doc = {
        '_id': str(uuid.uuid4()),
        'email': email,
        'user_id': user_id,
        'purpose': 'registration',
        'otp_hash': otp_hash,
        'attempts': 0,
        'used': False,
        'created_at': now.isoformat(),
        'expires_at': (now + timedelta(minutes=5)).isoformat()
    }

    otp_coll = get_collection('auth_otps')

    # Persist the generated code and pending account before sending email.
    # Verification consumes the code only after successful OTP verification.
    if codes_coll is not None:
        codes_coll.insert_one(code_doc)
    else:
        _memory_codes.append(code_doc)

    if coll is not None:
        coll.insert_one(new_user)
    else:
        _memory_users.append(new_user)

    if otp_coll is not None:
        otp_coll.update_many(
            {'email': email, 'purpose': 'registration', 'used': False},
            {'$set': {'used': True}}
        )
        otp_coll.insert_one(otp_doc)
    else:
        for item in _memory_otps:
            if item.get('email') == email and item.get('purpose') == 'registration' and not item.get('used', False):
                item['used'] = True
        _memory_otps.append(otp_doc)

    code_sent = email_service.send_institution_code_email(email, full_name, institution_code)
    otp_sent = email_service.send_registration_otp_email(email, full_name, otp)

    if not code_sent or not otp_sent:
        current_app.logger.error('Registration email delivery failed for %s', email)
        return jsonify({
            'error': 'Your account was created, but an email could not be delivered. Use Resend Code or contact the administrator.'
        }), 500

    return jsonify({
        'success': True,
        'requires_otp': True,
        'message': 'Registration started. Check your email for your institution code and verification OTP.',
        'data': {'email': email}
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Validate credentials and send a login OTP."""
    data = request.get_json() or {}

    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400

    email = str(data['email']).strip().lower()
    password = str(data['password'])

    coll = get_users_collection()

    if coll is not None:
        user = coll.find_one({'email': email})
    else:
        user = next(
            (u for u in _memory_users if u.get('email') == email),
            None
        )

    if not user:
        AuditLogger.log_user_login(email, success=False)
        return jsonify({'error': 'Invalid credentials'}), 401

    stored_password = user.get('password', '')

    if not bcrypt.checkpw(
        password.encode('utf-8'),
        stored_password.encode('utf-8')
    ):
        AuditLogger.log_user_login(email, success=False)
        return jsonify({'error': 'Invalid credentials'}), 401

    if user.get('email_verified') is False:
        return jsonify({
            'error': 'Please verify your email before logging in.',
            'requires_registration_otp': True
        }), 403



    if user.get('status') == 'pending':
        return jsonify({
            'error': 'Your account is pending admin approval. You will be notified once approved.'
        }), 403

    if user.get('status') != 'active':
        return jsonify({'error': 'Account is not active'}), 403

    user_id = str(user.get('_id') or user.get('id'))

    # Generate a secure 6-digit OTP.
    otp = f"{secrets.randbelow(1000000):06d}"
    otp_hash = bcrypt.hashpw(
        otp.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=5)

    otp_doc = {
        '_id': str(uuid.uuid4()),
        'email': email,
        'user_id': user_id,
        'purpose': 'login',
        'otp_hash': otp_hash,
        'attempts': 0,
        'used': False,
        'created_at': now.isoformat(),
        'expires_at': expires_at.isoformat()
    }

    # Invalidate previous login OTPs for this email.
    otp_coll = get_collection('auth_otps')

    if otp_coll is not None:
        otp_coll.update_many(
            {
                'email': email,
                'purpose': 'login',
                'used': False
            },
            {'$set': {'used': True}}
        )
        otp_coll.insert_one(otp_doc)
    else:
        for item in _memory_otps:
            if (
                item.get('email') == email
                and item.get('purpose') == 'login'
                and not item.get('used', False)
            ):
                item['used'] = True

        _memory_otps.append(otp_doc)

    # Send OTP by email.
    sent = send_login_otp_email(
        user['email'],
        user.get('full_name', 'User'),
        otp
    )

    if not sent:
        return jsonify({
            'error': 'Could not send verification code. Please try again.'
        }), 500

    return jsonify({
        'success': True,
        'requires_otp': True,
        'message': 'Verification code sent to your email',
        'data': {
            'email': email
        }
    }), 200



@auth_bp.route('/verify-registration-otp', methods=['POST'])
def verify_registration_otp():
    """Verify a registration OTP and mark the user's email verified."""
    data = request.get_json() or {}
    email = str(data.get('email', '')).strip().lower()
    otp = str(data.get('otp', '')).strip()

    if not email or not otp:
        return jsonify({'error': 'Email and OTP are required'}), 400

    if not otp.isdigit() or len(otp) != 6:
        return jsonify({'error': 'OTP must be a 6-digit code'}), 400

    otp_coll = get_collection('auth_otps')
    users_coll = get_users_collection()

    query = {
        'email': email,
        'purpose': 'registration',
        'used': False
    }

    if otp_coll is not None:
        challenge = otp_coll.find_one(query, sort=[('created_at', -1)])
    else:
        candidates = [
            item for item in _memory_otps
            if item.get('email') == email
            and item.get('purpose') == 'registration'
            and not item.get('used', False)
        ]
        challenge = max(
            candidates, key=lambda item: item.get('created_at', '')
        ) if candidates else None

    if not challenge:
        return jsonify({
            'error': 'No active registration code. Please register again or request a new code.'
        }), 400

    try:
        expires_at = datetime.fromisoformat(challenge['expires_at'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'error': 'Invalid verification session'}), 400

    if datetime.utcnow() > expires_at:
        if otp_coll is not None:
            otp_coll.update_one(
                {'_id': challenge['_id'], 'used': False},
                {'$set': {'used': True}}
            )
        else:
            challenge['used'] = True

        return jsonify({'error': 'Code expired. Please request a new code.'}), 400

    if challenge.get('attempts', 0) >= 5:
        return jsonify({
            'error': 'Too many incorrect attempts. Request a new code.'
        }), 429

    if not bcrypt.checkpw(
        otp.encode('utf-8'),
        challenge['otp_hash'].encode('utf-8')
    ):
        if otp_coll is not None:
            otp_coll.update_one(
                {'_id': challenge['_id'], 'used': False},
                {'$inc': {'attempts': 1}}
            )
        else:
            challenge['attempts'] = challenge.get('attempts', 0) + 1

        return jsonify({'error': 'Invalid verification code'}), 401

    user_id = str(challenge.get('user_id', ''))

    if users_coll is not None:
        user = users_coll.find_one({'_id': user_id})
    else:
        user = next(
            (
                item for item in _memory_users
                if str(item.get('_id') or item.get('id')) == user_id
            ),
            None
        )

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.get('email_verified') is True:
        return jsonify({'error': 'Email is already verified'}), 400

    institution_code = str(
        user.get('institution_code', '')
    ).strip().upper()

    codes_coll = get_collection('institution_codes')

    if codes_coll is not None:
        code_doc = codes_coll.find_one({
            'code': institution_code,
            'used': False
        })

        if not code_doc:
            return jsonify({
                'error': 'Institution code is no longer available'
            }), 409

        result = codes_coll.update_one(
            {'_id': code_doc['_id'], 'used': False},
            {'$set': {
                'used': True,
                'used_by': user_id,
                'used_at': datetime.utcnow().isoformat()
            }}
        )

        if result.modified_count != 1:
            return jsonify({
                'error': 'Institution code is no longer available'
            }), 409
    else:
        code_doc = next(
            (
                item for item in _memory_codes
                if item.get('code') == institution_code
                and not item.get('used', False)
            ),
            None
        )

        if not code_doc:
            return jsonify({
                'error': 'Institution code is no longer available'
            }), 409

        code_doc.update({
            'used': True,
            'used_by': user_id,
            'used_at': datetime.utcnow().isoformat()
        })

    now_iso = datetime.utcnow().isoformat()

    if users_coll is not None:
        result = users_coll.update_one(
            {'_id': user_id, 'email_verified': False},
            {'$set': {
                'email_verified': True,
                'updated_at': now_iso
            }}
        )

        if result.modified_count != 1:
            current_app.logger.error(
                'Institution code consumed but user verification update failed: %s',
                user_id
            )
            return jsonify({
                'error': 'Verification update failed. Contact support.'
            }), 500
    else:
        user['email_verified'] = True
        user['updated_at'] = now_iso

    if otp_coll is not None:
        otp_coll.update_one(
            {'_id': challenge['_id'], 'used': False},
            {'$set': {'used': True, 'verified_at': now_iso}}
        )
    else:
        challenge['used'] = True
        challenge['verified_at'] = now_iso

    try:
        send_welcome_email(user['email'], user.get('full_name', 'User'))
    except Exception:
        current_app.logger.exception('Welcome email failed after verification')

    return jsonify({
        'success': True,
        'message': 'Email verified. Please log in to continue.',
        'data': {'email': email}
    }), 200


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify the login OTP and issue JWT tokens."""
    data = request.get_json() or {}

    email = str(data.get('email', '')).strip().lower()
    otp = str(data.get('otp', '')).strip()

    if not email or not otp:
        return jsonify({
            'error': 'Email and OTP are required'
        }), 400

    if not otp.isdigit() or len(otp) != 6:
        return jsonify({
            'error': 'OTP must be a 6-digit code'
        }), 400

    otp_coll = get_collection('auth_otps')

    if otp_coll is not None:
        challenge = otp_coll.find_one(
            {
                'email': email,
                'purpose': 'login',
                'used': False
            },
            sort=[('created_at', -1)]
        )
    else:
        candidates = [
            x for x in _memory_otps
            if (
                x.get('email') == email
                and x.get('purpose') == 'login'
                and not x.get('used', False)
            )
        ]
        challenge = max(
            candidates,
            key=lambda x: x.get('created_at', '')
        ) if candidates else None

    if not challenge:
        return jsonify({
            'error': 'No active verification code. Please request a new code.'
        }), 400

    try:
        expires_at = datetime.fromisoformat(
            challenge['expires_at']
        )
    except Exception:
        return jsonify({
            'error': 'Invalid verification session'
        }), 400

    if datetime.utcnow() > expires_at:
        if otp_coll is not None:
            otp_coll.update_one(
                {'_id': challenge['_id']},
                {'$set': {'used': True}}
            )
        else:
            challenge['used'] = True

        return jsonify({
            'error': 'Verification code has expired. Please request a new code.'
        }), 400

    if challenge.get('attempts', 0) >= 5:
        return jsonify({
            'error': 'Too many incorrect attempts. Please request a new code.'
        }), 429

    if not bcrypt.checkpw(
        otp.encode('utf-8'),
        challenge['otp_hash'].encode('utf-8')
    ):
        if otp_coll is not None:
            otp_coll.update_one(
                {'_id': challenge['_id']},
                {'$inc': {'attempts': 1}}
            )
        else:
            challenge['attempts'] = challenge.get('attempts', 0) + 1

        return jsonify({
            'error': 'Invalid verification code'
        }), 401

    user_id = str(challenge['user_id'])

    if otp_coll is not None:
        otp_coll.update_one(
            {'_id': challenge['_id']},
            {
                '$set': {
                    'used': True,
                    'verified_at': datetime.utcnow().isoformat()
                }
            }
        )
        users_coll = get_users_collection()
        user = users_coll.find_one({'_id': user_id}) if users_coll is not None else None
    else:
        challenge['used'] = True
        user = next(
            (
                u for u in _memory_users
                if str(u.get('_id') or u.get('id')) == user_id
            ),
            None
        )

    if not user:
        return jsonify({'error': 'User not found'}), 404

    AuditLogger.log_user_login(email, success=True)

    access_token = create_access_token(identity=user_id)
    refresh_token = create_refresh_token(identity=user_id)

    response = jsonify({
        'success': True,
        'message': 'Login successful',
        'data': {
            'user': {
                'id': user_id,
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role']
            },
            'token': access_token
        }
    })

    set_access_cookies(response, access_token)

    return response, 200


@auth_bp.route('/resend-registration-otp', methods=['POST'])
def resend_registration_otp():
    """Resend a registration OTP with a 60-second cooldown."""
    data = request.get_json() or {}
    email = str(data.get('email', '')).strip().lower()

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    users_coll = get_users_collection()
    otp_coll = get_collection('auth_otps')

    if users_coll is not None:
        user = users_coll.find_one({'email': email})
    else:
        user = next(
            (u for u in _memory_users if u.get('email') == email),
            None
        )

    if not user:
        return jsonify({'error': 'Registration account not found'}), 404

    if user.get('email_verified') is True:
        return jsonify({'error': 'Email is already verified'}), 400

    now = datetime.utcnow()

    if otp_coll is not None:
        latest = otp_coll.find_one(
            {'email': email, 'purpose': 'registration'},
            sort=[('created_at', -1)]
        )
    else:
        candidates = [
            item for item in _memory_otps
            if item.get('email') == email
            and item.get('purpose') == 'registration'
        ]
        latest = max(
            candidates,
            key=lambda item: item.get('created_at', '')
        ) if candidates else None

    if not latest:
        return jsonify({
            'error': 'No registration verification session found. Please register again.'
        }), 400

    try:
        created_at = datetime.fromisoformat(latest['created_at'])
        elapsed = (now - created_at).total_seconds()

        if elapsed < 60:
            remaining = max(1, int(60 - elapsed))
            return jsonify({
                'error': f'Please wait {remaining} seconds before requesting another code.'
            }), 429
    except (KeyError, TypeError, ValueError):
        current_app.logger.warning(
            'Invalid registration OTP timestamp for %s', email
        )

    otp = f"{secrets.randbelow(1000000):06d}"
    otp_hash = bcrypt.hashpw(
        otp.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    user_id = str(user.get('_id') or user.get('id'))

    otp_doc = {
        '_id': str(uuid.uuid4()),
        'email': email,
        'user_id': user_id,
        'purpose': 'registration',
        'otp_hash': otp_hash,
        'attempts': 0,
        'used': False,
        'created_at': now.isoformat(),
        'expires_at': (now + timedelta(minutes=5)).isoformat()
    }

    if otp_coll is not None:
        otp_coll.update_many(
            {
                'email': email,
                'purpose': 'registration',
                'used': False
            },
            {'$set': {'used': True}}
        )
        otp_coll.insert_one(otp_doc)
    else:
        for item in _memory_otps:
            if (
                item.get('email') == email
                and item.get('purpose') == 'registration'
                and not item.get('used', False)
            ):
                item['used'] = True
        _memory_otps.append(otp_doc)

    if not email_service.enabled:
        return jsonify({'error': 'Email delivery is not configured.'}), 503

    code = user.get('institution_code')
    code_sent = bool(code) and email_service.send_institution_code_email(
        user['email'], user.get('full_name', 'User'), code
    )
    otp_sent = email_service.send_registration_otp_email(
        user['email'], user.get('full_name', 'User'), otp
    )

    if not code_sent or not otp_sent:
        return jsonify({
            'error': 'Could not send registration emails. Please try again later.'
        }), 500

    return jsonify({
        'success': True,
        'message': 'A new registration verification code has been sent.'
    }), 200


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend a login OTP, respecting a 60-second cooldown."""
    data = request.get_json() or {}
    email = str(data.get('email', '')).strip().lower()

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    otp_coll = get_collection('auth_otps')
    users_coll = get_users_collection()

    if users_coll is not None:
        user = users_coll.find_one({'email': email})
    else:
        user = next(
            (u for u in _memory_users if u.get('email') == email),
            None
        )

    if not user:
        return jsonify({'error': 'Unable to send verification code'}), 404

    now = datetime.utcnow()

    if otp_coll is not None:
        latest = otp_coll.find_one(
            {
                'email': email,
                'purpose': 'login'
            },
            sort=[('created_at', -1)]
        )
    else:
        candidates = [
            x for x in _memory_otps
            if x.get('email') == email and x.get('purpose') == 'login'
        ]
        latest = max(
            candidates,
            key=lambda x: x.get('created_at', '')
        ) if candidates else None

    if latest:
        try:
            created_at = datetime.fromisoformat(latest['created_at'])
            elapsed = (now - created_at).total_seconds()

            if elapsed < 60:
                remaining = int(60 - elapsed)
                return jsonify({
                    'error': f'Please wait {remaining} seconds before requesting another code.'
                }), 429
        except Exception:
            pass

    otp = f"{secrets.randbelow(1000000):06d}"
    otp_hash = bcrypt.hashpw(
        otp.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    otp_doc = {
        '_id': str(uuid.uuid4()),
        'email': email,
        'user_id': str(user.get('_id') or user.get('id')),
        'purpose': 'login',
        'otp_hash': otp_hash,
        'attempts': 0,
        'used': False,
        'created_at': now.isoformat(),
        'expires_at': (now + timedelta(minutes=5)).isoformat()
    }

    if otp_coll is not None:
        otp_coll.update_many(
            {
                'email': email,
                'purpose': 'login',
                'used': False
            },
            {'$set': {'used': True}}
        )
        otp_coll.insert_one(otp_doc)
    else:
        for item in _memory_otps:
            if (
                item.get('email') == email
                and item.get('purpose') == 'login'
                and not item.get('used', False)
            ):
                item['used'] = True

        _memory_otps.append(otp_doc)

    sent = send_login_otp_email(
        user['email'],
        user.get('full_name', 'User'),
        otp
    )

    if not sent:
        return jsonify({
            'error': 'Could not send verification code'
        }), 500

    return jsonify({
        'success': True,
        'message': 'A new verification code has been sent'
    }), 200

# ... (rest of auth routes: refresh, logout, me, forgot-password)
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_token = create_access_token(identity=user_id)
    response = jsonify({'success': True, 'message': 'Token refreshed'})
    set_access_cookies(response, new_token)
    return response, 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = jsonify({'success': True, 'message': 'Logged out successfully'})
    unset_jwt_cookies(response)
    return response, 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    coll = get_users_collection()
    
    if coll is not None:
        user = coll.find_one({'_id': user_id})
    else:
        user = next((u for u in _memory_users if u.get('_id') == user_id or u.get('id') == user_id), None)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'data': {
            'user': {
                'id': user.get('_id') or user.get('id'),
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role']
            }
        }
    }), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400
    return jsonify({
        'success': True,
        'message': 'Password reset link sent to your email'
    }), 200
