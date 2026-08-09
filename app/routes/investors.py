"""
Investor API - Complete investor management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import json
import os
from datetime import datetime

investors_bp = Blueprint('investors', __name__)

INVESTOR_FILE = './data/investors.json'

def get_investors_data():
    try:
        with open(INVESTOR_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'investors': []}

def save_investors_data(data):
    os.makedirs(os.path.dirname(INVESTOR_FILE), exist_ok=True)
    with open(INVESTOR_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@investors_bp.route('/', methods=['GET'])
@jwt_required()
def list_investors():
    data = get_investors_data()
    return jsonify({'success': True, 'data': data['investors']}), 200

@investors_bp.route('/<investor_id>', methods=['GET'])
@jwt_required()
def get_investor(investor_id):
    data = get_investors_data()
    for investor in data['investors']:
        if investor['investor_id'] == investor_id:
            return jsonify({'success': True, 'data': investor}), 200
    return jsonify({'error': 'Investor not found'}), 404

@investors_bp.route('/', methods=['POST'])
@jwt_required()
def create_investor():
    data = request.get_json()
    required_fields = ['firm_name', 'focus', 'investment_stage']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    investors_data = get_investors_data()
    new_investor = {
        'investor_id': f'INV-{len(investors_data["investors"]) + 1:04d}',
        **data,
        'created_at': datetime.utcnow().isoformat()
    }
    investors_data['investors'].append(new_investor)
    save_investors_data(investors_data)
    return jsonify({'success': True, 'data': new_investor}), 201

@investors_bp.route('/match', methods=['POST'])
@jwt_required()
def match_investors():
    data = request.get_json()
    if not data or 'startup_data' not in data:
        return jsonify({'error': 'Startup data required'}), 400
    investors_data = get_investors_data()
    matches = []
    for investor in investors_data['investors']:
        score = 50
        if investor.get('preferred_sectors'):
            for sector in investor['preferred_sectors']:
                if sector in data['startup_data'].get('sector', ''):
                    score += 20
        if investor.get('investment_stage'):
            score += 10
        matches.append({
            'investor_id': investor['investor_id'],
            'name': investor['firm_name'],
            'focus': investor['focus'],
            'stage': investor['investment_stage'],
            'match_percentage': min(score, 100)
        })
    matches.sort(key=lambda x: x['match_percentage'], reverse=True)
    return jsonify({'success': True, 'data': {'matches': matches[:10]}}), 200
