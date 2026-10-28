"""
Research Papers API - Curated papers with sector-based matching
"""

from app.utils.matching import score_paper
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import json
import os
from datetime import datetime

papers_bp = Blueprint('papers', __name__)

PAPER_FILE = './data/papers.json'

def get_papers_data():
    try:
        with open(PAPER_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'papers': []}

def save_papers_data(data):
    os.makedirs(os.path.dirname(PAPER_FILE), exist_ok=True)
    with open(PAPER_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@papers_bp.route('/', methods=['GET'])
@jwt_required()
def list_papers():
    data = get_papers_data()
    return jsonify({'success': True, 'data': data['papers']}), 200

@papers_bp.route('/<paper_id>', methods=['GET'])
@jwt_required()
def get_paper(paper_id):
    data = get_papers_data()
    for paper in data['papers']:
        if paper['paper_id'] == paper_id:
            return jsonify({'success': True, 'data': paper}), 200
    return jsonify({'error': 'Paper not found'}), 404

@papers_bp.route('/', methods=['POST'])
@jwt_required()
def create_paper():
    data = request.get_json()
    required_fields = ['title', 'author', 'takeaway', 'tags']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    papers_data = get_papers_data()
    new_paper = {
        'paper_id': f'P-{len(papers_data["papers"]) + 1:04d}',
        **data,
        'created_at': datetime.utcnow().isoformat()
    }
    papers_data['papers'].append(new_paper)
    save_papers_data(papers_data)
    return jsonify({'success': True, 'data': new_paper}), 201

@papers_bp.route('/match', methods=['POST'])
@jwt_required()
def match_papers():
    data = request.get_json()
    if not data or 'startup_data' not in data:
        return jsonify({'error': 'Startup data required'}), 400
    papers_data = get_papers_data()
    startup = data['startup_data'] or {}
    matches = []
    for paper in papers_data['papers']:
        score, reasons = score_paper(paper, startup)
        matches.append({
            'paper_id': paper['paper_id'],
            'title': paper['title'],
            'author': paper['author'],
            'takeaway': paper['takeaway'],
            'url': paper.get('url', ''),
            'match_percentage': score,
            'reasons': reasons
        })
    matches.sort(key=lambda x: x['match_percentage'], reverse=True)
    return jsonify({'success': True, 'data': {'matches': matches[:10]}}), 200
