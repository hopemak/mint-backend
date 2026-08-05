
"""
Workspace Routes
Real, persisted project comments/activity feed (JSON-file storage, same
pattern as evaluation.py — not MongoDB, not WebSockets/real-time yet).
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import os
from datetime import datetime
 
workspace_bp = Blueprint('workspace', __name__)
 
COMMENTS_FILE = './data/workspace_comments.json'
 
 
def get_comments():
    """Load all comments from file"""
    try:
        with open(COMMENTS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {'comments': []}
 
 
def save_comments(data):
    """Save all comments to file"""
    os.makedirs(os.path.dirname(COMMENTS_FILE), exist_ok=True)
    with open(COMMENTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
 
 
@workspace_bp.route('/<project_id>/comments', methods=['GET'])
@jwt_required()
def list_comments(project_id):
    """Get all comments for a project, newest first"""
    data = get_comments()
    project_comments = [c for c in data['comments'] if c.get('project_id') == project_id]
    project_comments.sort(key=lambda c: c.get('created_at', ''), reverse=True)
    return jsonify({'success': True, 'data': project_comments}), 200
 
 
@workspace_bp.route('/<project_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(project_id):
    """Post a new comment on a project, tied to the authenticated user"""
    body = request.get_json()
    if not body or not (body.get('text') or '').strip():
        return jsonify({'error': 'Comment text is required'}), 400
 
    user_id = get_jwt_identity()
    data = get_comments()
 
    new_comment = {
        'id': f'CMT-{len(data["comments"]) + 1:05d}',
        'project_id': project_id,
        'user_id': user_id,
        'author_name': (body.get('author_name') or 'Team member').strip(),
        'text': body['text'].strip(),
        'created_at': datetime.utcnow().isoformat(),
    }
    data['comments'].append(new_comment)
    save_comments(data)
 
    return jsonify({'success': True, 'data': new_comment}), 201