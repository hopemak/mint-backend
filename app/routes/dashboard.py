"""
Dashboard API - Real per-user statistics and trends
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from collections import defaultdict
from datetime import datetime

from app.database import get_collection

dashboard_bp = Blueprint('dashboard', __name__)

STARTUP_FILE = './data/startups.json'
MENTOR_FILE = './data/mentors.json'
FUNDING_REQUESTS = 'funding_requests'

MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
COLORS = ['#1D4241', '#4C8884', '#EF9C82', '#C7DAD8', '#8B5CF6', '#10B981', '#F59E0B']


def _load_json(path, key):
    try:
        with open(path, 'r') as f:
            return json.load(f).get(key, [])
    except Exception:
        return []


@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    user_id = get_jwt_identity()

    startups = _load_json(STARTUP_FILE, 'startups')
    my_startups = [s for s in startups if s.get('user_id') == user_id]

    mentors = _load_json(MENTOR_FILE, 'mentors')

    funding_collection = get_collection(FUNDING_REQUESTS)
    my_requests = list(funding_collection.find({'user_id': user_id}))

    total_funding = sum(
        r.get('approved_amount', r.get('amount', 0))
        for r in my_requests if r.get('status') == 'approved'
    )
    approved_count = len([r for r in my_requests if r.get('status') == 'approved'])
    success_rate = round((approved_count / len(my_requests)) * 100, 1) if my_requests else 0

    return jsonify({
        'success': True,
        'data': {
            'total_startups': len(my_startups),
            'mentors_active': len(mentors),
            'total_funding': total_funding,
            'success_rate': success_rate,
        }
    }), 200


@dashboard_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_trends():
    user_id = get_jwt_identity()

    funding_collection = get_collection(FUNDING_REQUESTS)
    my_requests = list(funding_collection.find({'user_id': user_id}))

    month_counts = defaultdict(lambda: {'submitted': 0, 'approved': 0})
    for r in my_requests:
        created = r.get('created_at')
        if not created:
            continue
        try:
            dt = datetime.fromisoformat(created)
        except ValueError:
            continue
        key = (dt.year, dt.month)
        month_counts[key]['submitted'] += 1
        if r.get('status') == 'approved':
            month_counts[key]['approved'] += 1

    sorted_months = sorted(month_counts.keys())[-6:]
    labels = [MONTH_NAMES[m - 1] for (y, m) in sorted_months]
    applications = [month_counts[k]['submitted'] for k in sorted_months]
    approvals = [month_counts[k]['approved'] for k in sorted_months]

    return jsonify({
        'success': True,
        'data': {
            'labels': labels,
            'applications': applications,
            'approvals': approvals,
        }
    }), 200


@dashboard_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    user_id = get_jwt_identity()

    startups = _load_json(STARTUP_FILE, 'startups')
    my_startups = [s for s in startups if s.get('user_id') == user_id]

    sector_counts = defaultdict(int)
    for s in my_startups:
        sector = s.get('sector') or 'Unspecified'
        sector_counts[sector] += 1

    return jsonify({
        'success': True,
        'data': {
            'sector_distribution': dict(sector_counts),
        }
    }), 200
