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


@public_stats_bp.route('/featured-startups', methods=['GET'])
def featured_startups():
    try:
        from app.routes.startups import get_startups
        items = (get_startups() or {}).get('startups', [])
    except Exception as exc:
        logger.warning('featured: startups unavailable: %s', exc)
        items = []

    def trl_of(s):
        try:
            return max(1, min(9, int(s.get('trl_level') or s.get('trl') or 0)))
        except (TypeError, ValueError):
            return 0

    rows = []
    for s in items:
        name = str(s.get('business_name') or '').strip()
        if not name or s.get('status') in ('rejected', 'draft'):
            continue
        rows.append({
            'id': s.get('startup_id') or name,
            'name': name,
            'sector': s.get('sector') or 'General',
            'trl': trl_of(s),
            'progress': round(trl_of(s) / 9 * 100),
            'created_at': s.get('created_at') or '',
        })
    rows.sort(key=lambda r: (r['trl'], r['created_at']), reverse=True)
    for r in rows:
        r.pop('created_at')
    return jsonify({'startups': rows[:3]}), 200


# ---------------- Testimonials ----------------
import uuid
from datetime import datetime
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity


@public_stats_bp.route('/testimonials', methods=['GET'])
def list_testimonials():
    coll = get_collection('testimonials')
    if coll is None:
        return jsonify({'testimonials': []}), 200
    docs = coll.find({'status': 'approved'}).sort('created_at', -1).limit(6)
    return jsonify({'testimonials': [
        {'id': d['_id'], 'quote': d.get('quote', ''),
         'name': d.get('name', ''), 'company': d.get('company', '')}
        for d in docs
    ]}), 200


@public_stats_bp.route('/testimonials', methods=['POST'])
@jwt_required()
def submit_testimonial():
    data = request.get_json() or {}
    quote = str(data.get('quote', '')).strip()
    company = str(data.get('company', '')).strip()
    if len(quote) < 20 or len(quote) > 400:
        return jsonify({'error': 'Testimonial must be 20-400 characters'}), 400
    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': get_jwt_identity()}) if users is not None else None
    if not user:
        return jsonify({'error': 'User not found'}), 404
    coll = get_collection('testimonials')
    if coll is None:
        return jsonify({'error': 'Database unavailable'}), 503
    coll.insert_one({
        '_id': str(uuid.uuid4()), 'user_id': user['_id'],
        'name': user.get('full_name', 'Anonymous'), 'company': company,
        'quote': quote, 'status': 'pending',
        'created_at': datetime.utcnow().isoformat(),
    })
    _notify_new_testimonial(user.get('full_name', 'A founder'))
    return jsonify({'success': True, 'message': 'Submitted for admin approval'}), 201


@public_stats_bp.route('/testimonials/<tid>/approve', methods=['PUT'])
@jwt_required()
def approve_testimonial(tid):
    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': get_jwt_identity()}) if users is not None else None
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Admin only'}), 403
    coll = get_collection('testimonials')
    res = coll.update_one({'_id': tid}, {'$set': {'status': 'approved'}})
    _notify_testimonial(coll, tid, 'approved')
    return jsonify({'success': res.modified_count == 1}), 200


def _require_admin():
    users = get_collection(USERS_COLLECTION)
    user = users.find_one({'_id': get_jwt_identity()}) if users is not None else None
    return user if user and user.get('role') == 'admin' else None


@public_stats_bp.route('/testimonials/admin', methods=['GET'])
@jwt_required()
def admin_list_testimonials():
    if not _require_admin():
        return jsonify({'error': 'Admin only'}), 403
    coll = get_collection('testimonials')
    docs = coll.find({}).sort('created_at', -1).limit(100) if coll is not None else []
    return jsonify({'testimonials': [
        {'id': d['_id'], 'quote': d.get('quote', ''), 'name': d.get('name', ''),
         'company': d.get('company', ''), 'status': d.get('status', 'pending'),
         'created_at': d.get('created_at', '')}
        for d in docs
    ]}), 200


@public_stats_bp.route('/testimonials/<tid>/reject', methods=['PUT'])
@jwt_required()
def reject_testimonial(tid):
    if not _require_admin():
        return jsonify({'error': 'Admin only'}), 403
    coll = get_collection('testimonials')
    res = coll.update_one({'_id': tid}, {'$set': {'status': 'rejected'}})
    _notify_testimonial(coll, tid, 'rejected')
    return jsonify({'success': res.modified_count == 1}), 200


# ---------------- Innovation map ----------------
REGIONS = ['Tigray', 'Afar', 'Amhara', 'Benishangul-Gumuz', 'Dire Dawa', 'Harari', 'Gambela',
           'Oromia', 'Somali', 'Addis Ababa', 'Sidama', 'Central Ethiopia',
           'South Ethiopia', 'South West Ethiopia']
_ALIASES = {'ADDIS ABEBA': 'Addis Ababa', 'ADDIS ABABA': 'Addis Ababa', 'OROMIA': 'Oromia',
            'OROMIYA': 'Oromia', 'BENISHANGUL GUMUZ': 'Benishangul-Gumuz',
            'BENISHANGUL-GUMUZ': 'Benishangul-Gumuz', 'DIRE DAWA': 'Dire Dawa',
            'SOUTH WEST': 'South West Ethiopia', 'SOUTH WEST ETHIOPIA': 'South West Ethiopia',
            'SOUTH ETHIOPIA': 'South Ethiopia', 'CENTRAL ETHIOPIA': 'Central Ethiopia'}
for _r in REGIONS:
    _ALIASES.setdefault(_r.upper(), _r)


@public_stats_bp.route('/regions', methods=['GET'])
def public_regions():
    try:
        from app.routes.startups import get_startups
        items = (get_startups() or {}).get('startups', [])
    except Exception as exc:
        logger.warning('regions: startups unavailable: %s', exc)
        items = []
    out = {r: {'count': 0, 'sectors': {}} for r in REGIONS}
    unassigned = 0
    for s in items:
        if s.get('status') in ('rejected', 'draft') or not str(s.get('business_name') or '').strip():
            continue
        region = _ALIASES.get(' '.join(str(s.get('region') or '').upper().split()))
        if not region:
            unassigned += 1
            continue
        out[region]['count'] += 1
        sec = str(s.get('sector') or 'General').strip() or 'General'
        out[region]['sectors'][sec] = out[region]['sectors'].get(sec, 0) + 1
    return jsonify({'regions': out, 'unassigned': unassigned}), 200



def _notify_testimonial(coll, tid, status):
    try:
        from app.notifications import notify
        d = coll.find_one({'_id': tid})
        if d:
            msg = ('Your testimonial is now public on the landing page.' if status == 'approved'
                   else 'Your testimonial was not approved.')
            notify(d['user_id'], 'Testimonial ' + status, msg, '/share-story')
    except Exception:
        pass


def _notify_new_testimonial(name):
    try:
        from app.notifications import notify_admins
        notify_admins('New testimonial to review', name + ' submitted a testimonial.', '/admin/testimonials')
    except Exception:
        pass
