from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
import json
import os
import uuid
from app.idea_notify import attach_owner, notify_idea_decision

ideas_bp = Blueprint('ideas', __name__, url_prefix='/api/ideas')

DATA_DIR = './data'
IDEAS_FILE = os.path.join(DATA_DIR, 'ideas.json')

def load_ideas():
    try:
        with open(IDEAS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'ideas': []}

def save_ideas(ideas):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(IDEAS_FILE, 'w') as f:
        json.dump(ideas, f, indent=2)

@ideas_bp.route('', methods=['GET'])  # No trailing slash
def get_ideas():
    ideas = load_ideas()
    return jsonify({'success': True, 'data': ideas['ideas'], 'total': len(ideas['ideas'])}), 200

@ideas_bp.route('', methods=['POST'])  # No trailing slash
def create_idea():
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    idea = {
        'id': f"IDEA-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
        'title': data.get('title'),
        'problem': data.get('problem', ''),
        'solution': data.get('solution', ''),
        'category': data.get('category', 'General'),
        'industry': data.get('industry', 'Technology'),
        'innovation_level': data.get('innovation_level', 5),
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat()
    }
    
    ideas = load_ideas()
    attach_owner(idea)
    ideas['ideas'].append(idea)
    save_ideas(ideas)
    
    return jsonify({'success': True, 'data': idea}), 201

@ideas_bp.route('/<idea_id>', methods=['GET'])
def get_idea(idea_id):
    ideas = load_ideas()
    for idea in ideas['ideas']:
        if idea.get('id') == idea_id:
            return jsonify({'success': True, 'data': idea}), 200
    return jsonify({'error': 'Idea not found'}), 404

@ideas_bp.route('/<idea_id>/evaluate', methods=['POST'])
def evaluate_idea(idea_id):
    import random
    
    ideas = load_ideas()
    idea = None
    for i in ideas['ideas']:
        if i.get('id') == idea_id:
            idea = i
            break
    
    if not idea:
        return jsonify({'error': 'Idea not found'}), 404
    
    # Calculate scores based on idea data
    innovation = idea.get('innovation_level', 5) * 10
    market = random.randint(60, 90)
    feasibility = random.randint(60, 90)
    financial = random.randint(60, 90)
    social = random.randint(60, 90)
    
    overall = int((innovation + market + feasibility + financial + social) / 5)
    
    result = {
        'overall_score': overall,
        'rating': 'Excellent' if overall >= 85 else 'Good' if overall >= 70 else 'Average',
        'innovation_score': innovation,
        'market_potential': market,
        'feasibility': feasibility,
        'financial_plan': financial,
        'social_impact': social,
        'team_capability': 70,
        'technical_complexity': int((innovation + feasibility) / 2),
        'financial_viability': int((financial + market) / 2),
        'risk_score': 100 - overall,
        'approval_status': 'Approved' if overall >= 70 else 'Under Review',
        'swot_analysis': {
            'strengths': ['Strong technical team', 'Clear market need', 'Innovative approach'],
            'weaknesses': ['Limited resources', 'Competition', 'Market entry challenges'],
            'opportunities': ['Growing market', 'Partnership potential', 'Government support'],
            'threats': ['Competitors', 'Regulatory changes', 'Economic uncertainty']
        },
        'risk_analysis': [
            {'name': 'Technological', 'level': 'Medium' if overall < 70 else 'Low'},
            {'name': 'Market', 'level': 'Medium' if market < 70 else 'Low'},
            {'name': 'Regulatory', 'level': 'High'},
            {'name': 'Financial', 'level': 'Medium' if financial < 70 else 'Low'}
        ],
        'recommendations': [
            {'priority': 'High', 'title': 'Increase Innovation', 'description': 'Add unique features to differentiate from competitors and create a strong value proposition.'},
            {'priority': 'High', 'title': 'Strengthen Feasibility', 'description': 'Break down implementation into smaller phases and create a detailed project roadmap.'},
            {'priority': 'Medium', 'title': 'Expand Market Research', 'description': 'Conduct surveys and interviews with potential customers to validate market demand.'},
            {'priority': 'Medium', 'title': 'Refine Business Model', 'description': 'Develop a clear revenue model and identify cost-saving opportunities.'}
        ],
        'confidence_score': random.randint(70, 95)
    }
    
    result['approval_status'] = 'Pending Review'
    return jsonify({'success': True, 'data': result}), 200  # status stays pending until an admin decides
    # Update idea status
    for i, item in enumerate(ideas['ideas']):
        if item.get('id') == idea_id:
            if item.get('status') not in ('approved', 'rejected', 'revision_requested'):
                ideas['ideas'][i]['status'] = 'evaluated'
            break
    save_ideas(ideas)
    
    return jsonify({'success': True, 'data': result}), 200

@ideas_bp.route('/<idea_id>', methods=['PUT'])
@jwt_required()
def update_idea(idea_id):
    data = request.get_json() or {}
    if 'status' in data:
        return jsonify({'error': 'Status can only be changed through the review route'}), 400
    ideas = load_ideas()
    
    for idea in ideas['ideas']:
        if idea.get('id') == idea_id:
            # Update allowed fields
            allowed = ['title', 'problem', 'solution', 'category', 'industry', 'innovation_level']
            for field in allowed:
                if field in data:
                    idea[field] = data[field]
            idea['updated_at'] = datetime.utcnow().isoformat()
            save_ideas(ideas)
            return jsonify({'success': True, 'data': idea}), 200
    
    return jsonify({'error': 'Idea not found'}), 404



# ---------------------------------------------------------------
# ADMIN REVIEW (scores and rules are calculated on the server)
# ---------------------------------------------------------------
import logging
from flask import g
from app.admin_guard import admin_required
from app.database import get_collection
from app.review_rules import (
    CRITERIA, clean_scores, compute_total, suggested_decision, check_decision
)

_log = logging.getLogger(__name__)


@ideas_bp.route('/review-rules', methods=['GET'])
def review_rules():
    from app import review_rules as r
    return jsonify({'success': True, 'data': {
        'criteria': r.CRITERIA, 'reject_codes': r.REJECT_CODES,
        'hard_reject_codes': r.HARD_REJECT_CODES, 'approve_min': r.APPROVE_MIN,
        'revision_min': r.REVISION_MIN, 'min_text': r.MIN_TEXT,
    }}), 200


@ideas_bp.route('/<idea_id>/review', methods=['POST'])
@admin_required
def review_idea(idea_id):
    data = request.get_json(silent=True) or {}

    scores, err = clean_scores(data.get('scores'))
    if err:
        return jsonify({'error': err}), 400
    total = compute_total(scores)

    decision = data.get('decision')
    comment = (data.get('comment') or '').strip()
    reason_code = data.get('reason_code')
    override = (data.get('override_reason') or '').strip()

    err = check_decision(decision, total, comment, reason_code, override)
    if err:
        return jsonify({'error': err}), 400

    ideas = load_ideas()
    for idea in ideas['ideas']:
        if idea.get('id') != idea_id:
            continue
        if idea.get('status') in ('approved', 'rejected'):
            return jsonify({'error': 'This idea already has a final decision'}), 409

        now = datetime.utcnow().isoformat()
        admin = g.admin_user
        review = {
            'scores': scores,
            'total': total,
            'suggested': suggested_decision(total),
            'decision': decision,
            'reason_code': reason_code if decision == 'rejected' else None,
            'comment': comment,
            'override_reason': override or None,
            'reviewed_by': str(admin.get('_id') or admin.get('id')),
            'reviewed_by_email': admin.get('email'),
            'reviewed_at': now,
        }
        idea['review'] = review
        idea.setdefault('review_history', []).append(review)
        idea['status'] = decision
        idea['updated_at'] = now
        save_ideas(ideas)

        notify_idea_decision(idea)
        # Durable copy in MongoDB (the JSON file can be lost on redeploy)
        try:
            col = get_collection('idea_reviews')
            if col is not None:
                col.insert_one({**review, 'idea_id': idea_id, 'idea_title': idea.get('title')})
        except Exception as exc:
            _log.warning('Could not save review copy to MongoDB: %s', exc)

        return jsonify({'success': True, 'data': idea}), 200

    return jsonify({'error': 'Idea not found'}), 404


@ideas_bp.route('/<idea_id>/notify-owner', methods=['POST'])
@admin_required
def notify_owner(idea_id):
    """Admin tool: tell an innovator about the decision on an idea.
    For ideas submitted before owners were recorded, send the innovator's email once."""
    import re
    from app.database import get_collection
    from app.idea_notify import notify_idea_decision

    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip()

    ideas = load_ideas()
    idea = next((i for i in ideas['ideas'] if i.get('id') == idea_id), None)
    if not idea:
        return jsonify({'error': 'Idea not found'}), 404
    if idea.get('status') not in ('approved', 'rejected', 'revision_requested'):
        return jsonify({'error': 'This idea has no decision yet. Review it first.'}), 400

    if email:
        users = get_collection('users')
        user = None
        if users is not None:
            user = users.find_one({'email': {'$regex': '^' + re.escape(email) + '$', '$options': 'i'}})
        if not user:
            return jsonify({'error': 'No user with that email'}), 404
        idea['owner_id'] = str(user.get('_id') or user.get('id'))
        save_ideas(ideas)
    if not idea.get('owner_id'):
        return jsonify({'error': 'This idea has no owner. Send the innovator email.'}), 400

    notify_idea_decision(idea)
    return jsonify({'success': True, 'message': 'Notification sent', 'status': idea.get('status')}), 200
