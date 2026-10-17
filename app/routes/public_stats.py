"""Public landing-page statistics (no authentication)."""
import logging
from flask import Blueprint, jsonify
from app.database import get_collection, USERS_COLLECTION

logger = logging.getLogger(__name__)
public_stats_bp = Blueprint('public_stats', __name__, url_prefix='/api/public')


@public_stats_bp.route('/stats', methods=['GET'])
def public_stats():
    startups = 0
    funding = 0
    mentors = 0

    try:
        from app.routes.startups import get_startups
        startups = len((get_startups() or {}).get('startups', []))
    except Exception as exc:
        logger.warning('stats: startups unavailable: %s', exc)

    try:
        from app.routes.funding import FUNDING_REQUESTS
        coll = get_collection(FUNDING_REQUESTS)
        if coll is not None:
            funding = sum(
                float(r.get('approved_amount') or 0)
                for r in coll.find({'status': 'approved'})
            )
    except Exception as exc:
        logger.warning('stats: funding unavailable: %s', exc)

    try:
        users = get_collection(USERS_COLLECTION)
        if users is not None:
            mentors = users.count_documents({'role': 'mentor', 'status': 'active'})
    except Exception as exc:
        logger.warning('stats: mentors unavailable: %s', exc)

    return jsonify({'startups': startups, 'funding_raised': funding, 'mentors': mentors}), 200
