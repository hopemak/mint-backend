"""
Mentor API - Complete mentor management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.audit import log_action
from app.utils.decorators import admin_required
import json
import os
from datetime import datetime

mentors_bp = Blueprint('mentors', __name__)

MENTOR_FILE = './data/mentors.json'

def get_mentors_data():
    try:
        with open(MENTOR_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'mentors': []}

def save_mentors_data(data):
    os.makedirs(os.path.dirname(MENTOR_FILE), exist_ok=True)
    with open(MENTOR_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@mentors_bp.route('/', methods=['GET'])
@jwt_required()
def list_mentors():
    data = get_mentors_data()
    return jsonify({'success': True, 'data': data['mentors']}), 200

@mentors_bp.route('/<mentor_id>', methods=['GET'])
@jwt_required()
def get_mentor(mentor_id):
    data = get_mentors_data()
    for mentor in data['mentors']:
        if mentor['mentor_id'] == mentor_id:
            return jsonify({'success': True, 'data': mentor}), 200
    return jsonify({'error': 'Mentor not found'}), 404

@mentors_bp.route('/', methods=['POST'])
@admin_required
def create_mentor():
    data = request.get_json()
    required_fields = ['full_name', 'expertise_areas', 'years_experience']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    mentors_data = get_mentors_data()
    new_mentor = {
        'mentor_id': f'M-{len(mentors_data["mentors"]) + 1:04d}',
        **data,
        'created_at': datetime.utcnow().isoformat()
    }
    mentors_data['mentors'].append(new_mentor)
    save_mentors_data(mentors_data)
    log_action('MENTOR_CREATE', details={'full_name': new_mentor.get('full_name')}, status='success')
    return jsonify({'success': True, 'data': new_mentor}), 201

@mentors_bp.route('/match', methods=['POST'])
@jwt_required()
def match_mentors():
    data = request.get_json()
    if not data or 'startup_data' not in data:
        return jsonify({'error': 'Startup data required'}), 400
    mentors_data = get_mentors_data()
    matches = []
    for mentor in mentors_data['mentors']:
        score = 50
        if mentor.get('preferred_sectors'):
            for sector in mentor['preferred_sectors']:
                if sector in data['startup_data'].get('sector', ''):
                    score += 20
        if mentor.get('years_experience', 0) >= 10:
            score += 15
        matches.append({
            'mentor_id': mentor['mentor_id'],
            'name': mentor['full_name'],
            'expertise': mentor['expertise_areas'],
            'match_percentage': min(score, 100)
        })
    matches.sort(key=lambda x: x['match_percentage'], reverse=True)
    return jsonify({'success': True, 'data': {'matches': matches[:10]}}), 200
