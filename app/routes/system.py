"""System info endpoints"""
from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required

system_bp = Blueprint('system', __name__)


@system_bp.route('/routes', methods=['GET'])
@jwt_required()
def list_routes():
    routes = []
    for rule in current_app.url_map.iter_rules():
        methods = sorted(m for m in rule.methods if m not in ('HEAD', 'OPTIONS'))
        for m in methods:
            routes.append({'method': m, 'path': str(rule)})
    routes.sort(key=lambda r: (r['path'], r['method']))
    return jsonify({'success': True, 'data': routes}), 200
