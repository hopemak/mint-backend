"""
Evaluation Routes
Save and retrieve AI evaluation results
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
import json
import os
from datetime import datetime

evaluation_bp = Blueprint('evaluation', __name__)

EVALUATION_FILE = './data/evaluations.json'


def get_evaluations():
    """Load evaluations from file."""
    try:
        with open(EVALUATION_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {'evaluations': []}


def save_evaluations(evaluations):
    """Persist evaluations to file."""
    os.makedirs(os.path.dirname(EVALUATION_FILE), exist_ok=True)
    with open(EVALUATION_FILE, 'w') as f:
        json.dump(evaluations, f, indent=2)


# ── Save a new evaluation result ──────────────────────────────────────────────

@evaluation_bp.route('/save', methods=['POST', 'OPTIONS'])
@cross_origin(origins=["http://localhost:5173", "http://localhost:5174",
                        "http://localhost:5175", "http://localhost:5176", "*"])
@jwt_required()
def save_evaluation():
    """Save an AI evaluation result for the current user."""
    if request.method == 'OPTIONS':
        return '', 200

    data    = request.get_json() or {}
    user_id = get_jwt_identity()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    evaluations = get_evaluations()

    evaluation_id = f'EVA-{len(evaluations["evaluations"]) + 1:04d}'

    new_eval = {
        'evaluation_id':   evaluation_id,
        'user_id':         user_id,
        'startup_id':      data.get('startup_id', ''),
        'title':           data.get('title', 'Untitled'),
        'overall_score':   data.get('overall_score', 0),
        'rating':          data.get('rating', ''),
        'approval_status': data.get('approval_status', 'Under Review'),
        'scores': {
            'innovation':         data.get('scores', {}).get('innovation', 0),
            'feasibility':        data.get('scores', {}).get('feasibility', 0),
            'marketPotential':    data.get('scores', {}).get('marketPotential', 0),
            'technicalComplexity':data.get('scores', {}).get('technicalComplexity', 0),
            'socialImpact':       data.get('scores', {}).get('socialImpact', 0),
            'financialViability': data.get('scores', {}).get('financialViability', 0),
        },
        'swot':     data.get('swot', {}),
        'risks':    data.get('risks', []),
        'feedback': data.get('feedback', []),
        'created_at': datetime.utcnow().isoformat(),
    }

    evaluations['evaluations'].append(new_eval)
    save_evaluations(evaluations)

    print(f"✅ Saved evaluation {evaluation_id} for user {user_id}")
    return jsonify({'success': True, 'data': new_eval}), 201


# ── Get evaluation history for the current user ───────────────────────────────

@evaluation_bp.route('/my', methods=['GET', 'OPTIONS'])
@cross_origin(origins=["http://localhost:5173", "http://localhost:5174",
                        "http://localhost:5175", "http://localhost:5176", "*"])
@jwt_required()
def get_my_evaluations():
    """Return all saved evaluations for the current user, newest first."""
    if request.method == 'OPTIONS':
        return '', 200

    user_id     = get_jwt_identity()
    evaluations = get_evaluations()

    my_evals = [
        e for e in evaluations['evaluations']
        if e.get('user_id') == user_id
    ]
    # Newest first
    my_evals.sort(key=lambda e: e.get('created_at', ''), reverse=True)

    return jsonify({'success': True, 'data': my_evals}), 200


# ── Legacy: create evaluation for a startup (kept for backward compatibility) ─

@evaluation_bp.route('/<startup_id>', methods=['POST'])
@jwt_required()
def create_evaluation(startup_id):
    """Create evaluation for a startup (legacy endpoint)."""
    data    = request.get_json()
    user_id = get_jwt_identity()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    evaluations = get_evaluations()

    new_evaluation = {
        'evaluation_id': f'EVA-{len(evaluations["evaluations"]) + 1:04d}',
        'startup_id':    startup_id,
        'evaluator_id':  user_id,
        'scores':        data.get('scores', {}),
        'comments':      data.get('comments', ''),
        'created_at':    datetime.utcnow().isoformat(),
    }

    evaluations['evaluations'].append(new_evaluation)
    save_evaluations(evaluations)

    return jsonify({'success': True, 'data': new_evaluation}), 201


@evaluation_bp.route('/<startup_id>', methods=['GET'])
@jwt_required()
def get_evaluation(startup_id):
    """Get the most recent evaluation for a startup (legacy endpoint)."""
    evaluations = get_evaluations()

    matches = [
        e for e in evaluations['evaluations']
        if e.get('startup_id') == startup_id
    ]
    if not matches:
        return jsonify({'error': 'Evaluation not found'}), 404

    # Return the most recent one
    matches.sort(key=lambda e: e.get('created_at', ''), reverse=True)
    return jsonify({'success': True, 'data': matches[0]}), 200
