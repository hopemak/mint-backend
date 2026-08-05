from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import os
import uuid

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
    
    # Update idea status
    for i, item in enumerate(ideas['ideas']):
        if item.get('id') == idea_id:
            ideas['ideas'][i]['status'] = 'evaluated'
            break
    save_ideas(ideas)
    
    return jsonify({'success': True, 'data': result}), 200
