"""
Evaluation Routes
Startup evaluation and scoring
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import os
from datetime import datetime

evaluation_bp = Blueprint('evaluation', __name__)

EVALUATION_FILE = './data/evaluations.json'

def get_evaluations():
    """Get evaluations from file"""
    try:
        with open(EVALUATION_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'evaluations': []}

def save_evaluations(evaluations):
    """Save evaluations to file"""
    os.makedirs(os.path.dirname(EVALUATION_FILE), exist_ok=True)
    with open(EVALUATION_FILE, 'w') as f:
        json.dump(evaluations, f, indent=2)

@evaluation_bp.route('/<startup_id>', methods=['POST'])
@jwt_required()
def create_evaluation(startup_id):
    """Create evaluation for a startup"""
    data = request.get_json()
    user_id = get_jwt_identity()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    evaluations = get_evaluations()
    
    new_evaluation = {
        'evaluation_id': f'EVA-{len(evaluations["evaluations"]) + 1:04d}',
        'startup_id': startup_id,
        'evaluator_id': user_id,
        'scores': data.get('scores', {}),
        'comments': data.get('comments', ''),
        'created_at': datetime.utcnow().isoformat()
    }
    
    evaluations['evaluations'].append(new_evaluation)
    save_evaluations(evaluations)
    
    return jsonify({'success': True, 'data': new_evaluation}), 201

@evaluation_bp.route('/<startup_id>', methods=['GET'])
@jwt_required()
def get_evaluation(startup_id):
    """Get evaluation for a startup"""
    evaluations = get_evaluations()
    
    for eval_record in evaluations['evaluations']:
        if eval_record['startup_id'] == startup_id:
            return jsonify({'success': True, 'data': eval_record}), 200
    
    return jsonify({'error': 'Evaluation not found'}), 404
