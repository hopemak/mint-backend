"""
Grant Management API - Complete grant system
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.audit import log_action
from app.utils.decorators import admin_required
import json
import os
from datetime import datetime

grants_bp = Blueprint('grants', __name__)

GRANT_FILE = './data/grants.json'

def get_grants_data():
    try:
        with open(GRANT_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'grants': [], 'applications': []}

def save_grants_data(data):
    os.makedirs(os.path.dirname(GRANT_FILE), exist_ok=True)
    with open(GRANT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@grants_bp.route('/', methods=['GET'])
@jwt_required()
def list_grants():
    data = get_grants_data()
    return jsonify({'success': True, 'data': data['grants']}), 200

@grants_bp.route('/<grant_id>', methods=['GET'])
@jwt_required()
def get_grant(grant_id):
    data = get_grants_data()
    for grant in data['grants']:
        if grant['grant_id'] == grant_id:
            return jsonify({'success': True, 'data': grant}), 200
    return jsonify({'error': 'Grant not found'}), 404

@grants_bp.route('/', methods=['POST'])
@admin_required
def create_grant():
    data = request.get_json()
    required_fields = ['grant_name', 'program', 'max_amount', 'min_amount', 'deadline', 'sectors']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    grants_data = get_grants_data()
    new_grant = {
        'grant_id': f'G-{len(grants_data["grants"]) + 1:04d}',
        **data,
        'created_at': datetime.utcnow().isoformat(),
        'created_by': get_jwt_identity(),
        'funds_allocated': 0,
        'funds_remaining': data['max_amount'],
        'status': 'active'
    }
    grants_data['grants'].append(new_grant)
    save_grants_data(grants_data)
    return jsonify({'success': True, 'data': new_grant}), 201

@grants_bp.route('/<grant_id>', methods=['PUT'])
@admin_required
def update_grant(grant_id):
    data = request.get_json()
    grants_data = get_grants_data()
    for i, grant in enumerate(grants_data['grants']):
        if grant['grant_id'] == grant_id:
            allowed_fields = ['grant_name', 'program', 'max_amount', 'min_amount', 'deadline', 'sectors', 'status']
            for field in allowed_fields:
                if field in data:
                    grants_data['grants'][i][field] = data[field]
            grants_data['grants'][i]['updated_at'] = datetime.utcnow().isoformat()
            save_grants_data(grants_data)
            return jsonify({'success': True, 'message': 'Grant updated', 'data': grants_data['grants'][i]}), 200
    return jsonify({'error': 'Grant not found'}), 404

@grants_bp.route('/<grant_id>', methods=['DELETE'])
@admin_required
def delete_grant(grant_id):
    grants_data = get_grants_data()
    for i, grant in enumerate(grants_data['grants']):
        if grant['grant_id'] == grant_id:
            grants_data['grants'].pop(i)
            save_grants_data(grants_data)
            return jsonify({'success': True, 'message': 'Grant deleted'}), 200
    return jsonify({'error': 'Grant not found'}), 404

@grants_bp.route('/apply', methods=['POST'])
@jwt_required()
def apply_for_grant():
    data = request.get_json()
    user_id = get_jwt_identity()
    required_fields = ['grant_id', 'startup_id', 'amount_requested']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    grants_data = get_grants_data()
    grant_found = False
    for grant in grants_data['grants']:
        if grant['grant_id'] == data['grant_id']:
            grant_found = True
            if grant['funds_remaining'] < data['amount_requested']:
                return jsonify({'error': 'Insufficient funds'}), 400
            break
    if not grant_found:
        return jsonify({'error': 'Grant not found'}), 404
    for app in grants_data['applications']:
        if app['grant_id'] == data['grant_id'] and app['startup_id'] == data['startup_id']:
            return jsonify({'error': 'Already applied'}), 409
    application = {
        'application_id': f'GA-{len(grants_data["applications"]) + 1:04d}',
        'grant_id': data['grant_id'],
        'startup_id': data['startup_id'],
        'user_id': user_id,
        'amount_requested': data['amount_requested'],
        'status': 'pending',
        'notes': data.get('notes', ''),
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    grants_data['applications'].append(application)
    save_grants_data(grants_data)
    return jsonify({'success': True, 'message': 'Application submitted', 'data': application}), 201

@grants_bp.route('/match', methods=['POST'])
@jwt_required()
def match_grants():
    data = request.get_json()
    if not data or 'startup_data' not in data:
        return jsonify({'error': 'Startup data required'}), 400
    grants_data = get_grants_data()
    matches = []
    for grant in grants_data['grants']:
        score = 50
        if grant.get('sectors'):
            for sector in grant['sectors']:
                if sector in data['startup_data'].get('sector', ''):
                    score += 20
                    break
        deadline_str = grant.get('deadline')
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
                days_until = (deadline - datetime.utcnow()).days
                if 0 <= days_until <= 30:
                    score += 20
                elif 30 < days_until <= 90:
                    score += 10
            except ValueError:
                pass
        matches.append({
            'grant_id': grant['grant_id'],
            'name': grant['grant_name'],
            'type': grant.get('type', 'Government'),
            'deadline': grant.get('deadline'),
            'tags': grant.get('sectors', []),
            'amount': grant.get('max_amount', 0),
            'match_percentage': min(score, 100)
        })
    matches.sort(key=lambda x: x['match_percentage'], reverse=True)
    return jsonify({'success': True, 'data': {'matches': matches[:10]}}), 200

@grants_bp.route('/applications', methods=['GET'])
@jwt_required()
def list_applications():
    grants_data = get_grants_data()
    return jsonify({'success': True, 'data': grants_data['applications']}), 200

@grants_bp.route('/applications/<application_id>/status', methods=['PUT'])
@admin_required
def update_application_status(application_id):
    data = request.get_json()
    if 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
    grants_data = get_grants_data()
    for i, app in enumerate(grants_data['applications']):
        if app['application_id'] == application_id:
            grants_data['applications'][i]['status'] = data['status']
            grants_data['applications'][i]['updated_at'] = datetime.utcnow().isoformat()
            if data['status'] == 'approved':
                for grant in grants_data['grants']:
                    if grant['grant_id'] == app['grant_id']:
                        grant['funds_allocated'] += app['amount_requested']
                        grant['funds_remaining'] -= app['amount_requested']
                        break
            save_grants_data(grants_data)
            log_action('GRANT_APPLICATION_STATUS_UPDATE', details={'application_id': application_id, 'new_status': data['status']}, status='success')
            return jsonify({'success': True, 'message': 'Status updated', 'data': grants_data['applications'][i]}), 200
    return jsonify({'error': 'Application not found'}), 404
