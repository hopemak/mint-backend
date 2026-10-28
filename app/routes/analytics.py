"""
Analytics API - Real computed metrics from platform data
"""

from flask import Blueprint, jsonify
from app.utils.decorators import admin_required
from flask_jwt_extended import jwt_required
import json
from collections import defaultdict
from datetime import datetime

from app.database import get_collection

analytics_bp = Blueprint('analytics', __name__)

STARTUP_FILE = './data/startups.json'
IDEAS_FILE = './data/ideas.json'
MENTOR_FILE = './data/mentors.json'
GRANT_FILE = './data/grants.json'
EVENT_FILE = './data/events.json'
SESSION_FILE = './data/sessions.json'
FUNDING_REQUESTS = 'funding_requests'

MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
STAGE_COLORS = {
    'Idea': '#94A3B8',
    'Seed': '#1D4241',
    'Growth': '#4C8884',
    'Scale': '#EF9C82',
}
GENERIC_COLORS = ['#1D4241', '#4C8884', '#EF9C82', '#94A3B8', '#6366F1', '#F59E0B', '#EF4444', '#22D3EE']


def _load_json(path, key):
    try:
        with open(path, 'r') as f:
            return json.load(f).get(key, [])
    except Exception:
        return []


def _color_for(i):
    return GENERIC_COLORS[i % len(GENERIC_COLORS)]


@analytics_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    startups = _load_json(STARTUP_FILE, 'startups')
    ideas = _load_json(IDEAS_FILE, 'ideas')
    mentors = _load_json(MENTOR_FILE, 'mentors')
    grants_data = _load_json(GRANT_FILE, 'grants')
    grant_applications = _load_json(GRANT_FILE, 'applications')
    events = _load_json(EVENT_FILE, 'events')
    session_requests = _load_json(SESSION_FILE, 'requests')

    funding_collection = get_collection(FUNDING_REQUESTS)
    funding_requests = list(funding_collection.find())

    # --- Top stat cards ---
    active_startups = len(startups)
    ideas_submitted = len(ideas)
    total_funding = sum(
        r.get('approved_amount', r.get('amount', 0))
        for r in funding_requests if r.get('status') == 'approved'
    )
    mentors_count = len(mentors)
    jobs_created = sum(s.get("jobs_created", 0) for s in startups)

    # --- Startup Growth Trends: startups created per month, last 6 months chronologically ---
    growth_counts = defaultdict(int)
    for s in startups:
        created = s.get('created_at')
        if created:
            try:
                dt = datetime.fromisoformat(created)
                growth_counts[(dt.year, dt.month)] += 1
            except ValueError:
                pass
    sorted_months = sorted(growth_counts.keys())[-6:]
    growth_trend = [{'month': MONTH_NAMES[m - 1], 'value': growth_counts[(y, m)]} for (y, m) in sorted_months]

    # --- Funding Distribution by stage: requested (all) vs approved only ---
    def stage_breakdown(requests_subset):
        amounts = defaultdict(int)
        for r in requests_subset:
            stage = r.get('stage', 'Unspecified')
            amounts[stage] += r.get('amount', 0)
        total = sum(amounts.values()) or 1
        return [
            {
                'name': stage,
                'value': round((amount / total) * 100),
                'color': STAGE_COLORS.get(stage, '#CBD5E1'),
            }
            for stage, amount in amounts.items()
        ]

    funding_by_stage_requested = stage_breakdown(funding_requests)
    funding_by_stage_approved = stage_breakdown([r for r in funding_requests if r.get('status') == 'approved'])

    # --- Idea Submissions by quarter ---
    quarter_counts = defaultdict(lambda: {'submitted': 0, 'approved': 0})
    for idea in ideas:
        created = idea.get('created_at')
        if not created:
            continue
        try:
            dt = datetime.fromisoformat(created)
        except ValueError:
            continue
        q = (dt.month - 1) // 3 + 1
        key = f'Q{q} {dt.year}'
        quarter_counts[key]['submitted'] += 1
        if idea.get('status') == 'evaluated':
            quarter_counts[key]['approved'] += 1
    submissions_by_quarter = [
        {'q': k, 'submitted': v['submitted'], 'approved': v['approved']}
        for k, v in sorted(quarter_counts.items())
    ]

    # --- Regional Innovation Activity: real region field on startups ---
    region_counts = defaultdict(int)
    for s in startups:
        region = s.get('region') or 'Unspecified'
        region_counts[region] += 1
    regions = [{'region': r, 'index': c, 'change': 0} for r, c in region_counts.items()]

    # --- Sector Distribution of Startups ---
    sector_counts = defaultdict(int)
    for s in startups:
        sector = s.get('sector') or 'Unspecified'
        sector_counts[sector] += 1
    sector_distribution = [
        {'name': sector, 'value': count, 'color': _color_for(i)}
        for i, (sector, count) in enumerate(sector_counts.items())
    ]

    # --- Startup Status Breakdown ---
    status_counts = defaultdict(int)
    for s in startups:
        status = s.get('status') or 'Unspecified'
        status_counts[status] += 1
    status_distribution = [
        {'name': status, 'value': count, 'color': _color_for(i)}
        for i, (status, count) in enumerate(status_counts.items())
    ]

    # --- Funding Pipeline Summary (real dollar amounts) ---
    total_requested_amount = sum(r.get('amount', 0) for r in funding_requests)
    total_approved_amount = sum(
        r.get('approved_amount', r.get('amount', 0))
        for r in funding_requests if r.get('status') == 'approved'
    )
    total_pending_amount = sum(r.get('amount', 0) for r in funding_requests if r.get('status') == 'pending')
    funding_pipeline = {
        'requested': total_requested_amount,
        'approved': total_approved_amount,
        'pending': total_pending_amount,
    }

    # --- Grant Application Funnel ---
    grant_status_counts = defaultdict(int)
    for app in grant_applications:
        status = app.get('status') or 'Unspecified'
        grant_status_counts[status] += 1
    grant_funnel = [
        {'name': status, 'value': count, 'color': _color_for(i)}
        for i, (status, count) in enumerate(grant_status_counts.items())
    ]

    # --- Event Registrations ---
    total_event_registrations = sum(len(e.get('registered_users', [])) for e in events)
    event_registrations_by_event = [
        {'name': e.get('title', 'Untitled'), 'value': len(e.get('registered_users', []))}
        for e in events
    ]

    # --- Startup Success Forecast: Random Forest estimate for the real startups ---
    try:
        from app.routes.ml import forecast_success
        success_forecast = forecast_success(startups, _load_json('./data/evaluations.json', 'evaluations'))
    except Exception:
        success_forecast = None

    return jsonify({
        'success': True,
        'data': {
            'activeStartups': active_startups,
            'ideasSubmitted': ideas_submitted,
            'totalFunding': f'${total_funding:,}',
            'mentors': mentors_count,
            'jobsCreated': jobs_created,
            'growthTrend': growth_trend,
            'fundingByStage': funding_by_stage_approved,
            'fundingByStageRequested': funding_by_stage_requested,
            'fundingByStageApproved': funding_by_stage_approved,
            'submissionsByQuarter': submissions_by_quarter,
            'regions': regions,
            'sectorDistribution': sector_distribution,
            'statusDistribution': status_distribution,
            'fundingPipeline': funding_pipeline,
            'eventRegistrations': event_registrations_by_event,
            'successForecast': success_forecast,
        }
    }), 200


@analytics_bp.route('/forecast-debug', methods=['GET'])
def forecast_debug():
    import traceback
    try:
        from app.routes.ml import forecast_success
        result = forecast_success(
            _load_json('./data/startups.json', 'startups'),
            _load_json('./data/evaluations.json', 'evaluations'),
        )
        return jsonify({'ok': True, 'forecast': result})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e), 'trace': traceback.format_exc()}), 500
