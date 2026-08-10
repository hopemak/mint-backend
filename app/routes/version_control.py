"""
Version Control API - Real git log from the project repo
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
import subprocess

version_control_bp = Blueprint('version_control', __name__)

@version_control_bp.route('/commits', methods=['GET'])
@jwt_required()
def get_commits():
    try:
        result = subprocess.run(
            ['git', 'log', '-10', '--pretty=format:%H|%an|%ad|%s', '--date=short'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return jsonify({'success': False, 'error': 'Could not read git history'}), 500

        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            sha, author, date, message = line.split('|', 3)
            commits.append({
                'sha': sha[:7],
                'author': author,
                'date': date,
                'message': message,
            })

        return jsonify({'success': True, 'data': commits}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
