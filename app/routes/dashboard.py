"""
Dashboard API - Analytics and Statistics
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    return jsonify({
        'success': True,
        'data': {
            'total_startups': 150,
            'approved_startups': 45,
            'pending_startups': 30,
            'total_funding': 12500000,
            'mentors_active': 25,
            'investors_active': 18,
            'success_rate': 68.5,
            'total_jobs_created': 320,
            'total_revenue_generated': 45000000,
            'average_funding': 833333
        }
    }), 200

@dashboard_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_trends():
    return jsonify({
        'success': True,
        'data': {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'applications': [12, 15, 18, 22, 20, 25],
            'approvals': [8, 10, 12, 15, 14, 18],
            'funding': [1000000, 1200000, 1500000, 1800000, 2000000, 2500000]
        }
    }), 200

@dashboard_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    return jsonify({
        'success': True,
        'data': {
            'sector_distribution': {
                'Agriculture': 25,
                'Healthcare': 20,
                'FinTech': 18,
                'EdTech': 12,
                'CleanTech': 10,
                'Manufacturing': 8,
                'Biotech': 7
            },
            'stage_distribution': {
                'idea': 20,
                'prototype': 30,
                'mvp': 25,
                'seed': 15,
                'growth': 10
            }
        }
    }), 200
