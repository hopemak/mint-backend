"""Transparent, rule-based matching for mentors, investors, grants and papers.

Every score is a weighted average of simple, explainable factors (0 to 1 each):

    score = 100 x  sum(weight x fit) / sum(weights of the factors we can actually measure)

A factor is skipped when the data for it is missing, so missing data never lowers a score
and there is no hidden "50 free points". Each match also returns a list of plain-language
reasons, so the result can always be explained.
"""

import re
from datetime import datetime

# Words that mean the same field. Matching is done on these families, ignoring case,
# so "AgriTech", "agriculture" and "Farming" all count as the same sector.
GROUPS = {
    'agriculture': {'agritech', 'agriculture', 'agri', 'agribusiness', 'farming', 'farm', 'farmers', 'crop', 'crops', 'food', 'foodsecurity'},
    'health': {'healthtech', 'healthcare', 'health', 'medtech', 'medical', 'biotech', 'telemedicine', 'pharma', 'pharmaceutical'},
    'finance': {'fintech', 'finance', 'financial', 'banking', 'payments', 'insurance', 'investment', 'fundraising'},
    'education': {'edtech', 'education', 'school', 'students', 'teaching'},
    'clean': {'cleantech', 'energy', 'renewable', 'solar', 'environment', 'sustainability', 'sustainable', 'climate', 'greentech', 'water'},
    'ai': {'ai', 'ml', 'machinelearning', 'artificialintelligence', 'datascience', 'nlp', 'analytics', 'neural'},
    'logistics': {'logistics', 'supplychain', 'transport', 'ecommerce'},
}
# Broad words: any technology startup is a partial fit for them.
GENERIC_TECH = {'tech', 'technology', 'software', 'saas', 'digital', 'it', 'iot', 'innovation', 'development', 'engineering'}
GENERIC = 'generic_tech'
STOP = {'with', 'that', 'this', 'from', 'have', 'will', 'your', 'their', 'into', 'more', 'than', 'also', 'such', 'each', 'about',
        'which', 'where', 'while', 'using', 'based', 'high', 'real', 'time', 'help', 'provides', 'platform', 'solution', 'solutions'}


# Two-word phrases that must be read together ("machine learning" is AI, not education).
PHRASES = {
    'machine learning': 'machinelearning', 'artificial intelligence': 'artificialintelligence',
    'deep learning': 'machinelearning', 'computer vision': 'ai', 'data science': 'datascience',
    'supply chain': 'supplychain', 'food security': 'foodsecurity', 'renewable energy': 'renewable',
}


def _ids(text, is_startup=False):
    """Turn free text into a set of concept ids (sector families + meaningful words).
    Only the startup's own sector may be flagged as 'technology' just because it ends in 'tech'
    (AgriTech is a technology startup). A mentor who likes 'FinTech' is NOT a broad 'Tech' mentor."""
    text = str(text or '').lower()
    found = set()
    for phrase, joined in PHRASES.items():
        if phrase in text:
            text = text.replace(phrase, ' ' + joined + ' ')
    compact = re.sub(r'[^a-z0-9]', '', text)
    candidates = re.findall(r'[a-z0-9]+', text)
    if 0 < len(compact) <= 20:
        candidates.append(compact)
    for token in candidates:
        matched = False
        for family, words in GROUPS.items():
            if token in words:
                found.add(family)
                matched = True
        if token in GENERIC_TECH or (is_startup and token.endswith('tech')):
            found.add(GENERIC)
            matched = True
        if not matched and len(token) >= 4 and token not in STOP:
            found.add(token)
    return found


def _num(value, default=None):
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def sector_fit(startup_sector, targets):
    """1.0 same sector, 0.5 only a broad 'Tech'-type match, 0.0 no match, None if unknown."""
    if not startup_sector or not targets:
        return None, None
    if isinstance(targets, str):
        targets = [targets]
    s_ids = _ids(startup_sector, is_startup=True)
    s_key = re.sub(r'[^a-z0-9]', '', str(startup_sector).lower())
    best, why = 0.0, None
    for target in targets:
        t_key = re.sub(r'[^a-z0-9]', '', str(target).lower())
        t_ids = _ids(target)
        if t_key and t_key == s_key:
            return 1.0, f'Same sector: {target}'
        if (s_ids & t_ids) - {GENERIC}:
            return 1.0, f'Sector match: {target}'
        if GENERIC in s_ids and GENERIC in t_ids and best < 0.5:
            best, why = 0.5, f'Works with technology startups ({target})'
    return best, why


def text_fit(startup_text, target_text):
    """How many real concepts the two texts share (two or more = full fit). None if no text."""
    s = _ids(startup_text) - {GENERIC}
    t = _ids(target_text) - {GENERIC}
    if not s or not t:
        return None, None
    shared = s & t
    if not shared:
        return 0.0, None
    names = ', '.join(sorted(shared)[:3])
    return min(1.0, len(shared) / 2), f'Shared topics: {names}'


def weighted(factors):
    """factors: list of (weight, fit or None, reason). Returns (score 0-100, reasons)."""
    used = [f for f in factors if f[1] is not None]
    total = sum(w for w, _, _ in used)
    if not total:
        return 0, []
    score = 100 * sum(w * fit for w, fit, _ in used) / total
    return int(round(max(0, min(100, score)))), [r for _, fit, r in used if fit and r]


def startup_text(startup):
    return f"{startup.get('sector', '')} {str(startup.get('description', ''))[:1500]}"


def stage_rank_from_trl(startup):
    trl = _num(startup.get('trl_level'), _num(startup.get('trl')))
    if trl is None:
        return None
    return 1 if trl <= 3 else 2 if trl <= 7 else 3


def investor_stage_rank(stage):
    s = str(stage or '').lower()
    if any(k in s for k in ('pre-seed', 'preseed', 'idea', 'angel')):
        return 1
    if 'seed' in s:
        return 2
    if 'series a' in s or 'early' in s:
        return 3
    if any(k in s for k in ('series b', 'series c', 'growth', 'late', 'scale')):
        return 4
    return None


# ── Mentors ─────────────────────────────────────────────────────────────────

def score_mentor(mentor, startup):
    sector_f, sector_why = sector_fit(startup.get('sector'), mentor.get('preferred_sectors'))
    text_f, text_why = text_fit(startup_text(startup), f"{mentor.get('expertise_areas', '')} {mentor.get('bio', '')}")
    years = _num(mentor.get('years_experience'))
    rating = _num(mentor.get('rating'))
    availability = str(mentor.get('availability') or '').lower()
    avail_f = None if not availability else 1.0 if availability == 'available' else 0.3 if availability == 'busy' else 0.0
    return weighted([
        (40, sector_f, sector_why),
        (25, text_f, text_why),
        (15, None if years is None else min(years, 15) / 15, f'{int(years)} years of experience' if years else None),
        (10, None if rating is None else min(rating, 5) / 5, f'Rated {rating}/5' if rating else None),
        (10, avail_f, 'Available now' if avail_f == 1.0 else None),
    ])


# ── Investors ───────────────────────────────────────────────────────────────

def score_investor(investor, startup):
    sector_f, sector_why = sector_fit(startup.get('sector'), investor.get('preferred_sectors'))
    text_f, text_why = text_fit(startup_text(startup), f"{investor.get('focus', '')} {investor.get('description', '')}")
    s_rank, i_rank = stage_rank_from_trl(startup), investor_stage_rank(investor.get('investment_stage'))
    stage_f = None
    if s_rank is not None and i_rank is not None:
        gap = abs(s_rank - i_rank)
        stage_f = 1.0 if gap == 0 else 0.5 if gap == 1 else 0.0
    return weighted([
        (50, sector_f, sector_why),
        (35, stage_f, f"Stage fits: {investor.get('investment_stage')}" if stage_f else None),
        (15, text_f, text_why),
    ])


# ── Grants ──────────────────────────────────────────────────────────────────

def grant_is_open(grant, today=None):
    """Closed or past-deadline grants must not be recommended."""
    today = today or datetime.utcnow()
    if str(grant.get('status') or '').lower() in ('closed', 'inactive', 'expired', 'cancelled'):
        return False
    deadline = grant.get('deadline')
    if deadline:
        try:
            return (datetime.strptime(str(deadline)[:10], '%Y-%m-%d') - today).days >= 0
        except ValueError:
            return True
    return True


def score_grant(grant, startup, today=None):
    today = today or datetime.utcnow()
    # Some grants list a stage ("Seed Stage") among their sectors. Stages are not sectors.
    sectors = [s for s in (grant.get('sectors') or []) if 'stage' not in str(s).lower()]
    if any(str(s).strip().lower() == 'all' for s in sectors):
        sector_f, sector_why = 0.6, 'Open to all sectors'
    else:
        sector_f, sector_why = sector_fit(startup.get('sector'), sectors)

    urgency_f, urgency_why = None, None
    deadline = grant.get('deadline')
    if deadline:
        try:
            days = (datetime.strptime(str(deadline)[:10], '%Y-%m-%d') - today).days
            urgency_f = 1.0 if days <= 30 else 0.7 if days <= 90 else 0.4
            urgency_why = f'Deadline in {max(days, 0)} days'
        except ValueError:
            pass

    need, low, high = _num(startup.get('funding_needed')), _num(grant.get('min_amount')), _num(grant.get('max_amount'))
    funding_f, funding_why = None, None
    if need and need > 0 and high:
        if low is not None and low <= need <= high:
            funding_f, funding_why = 1.0, 'Funding need is within the grant range'
        elif need > high:
            funding_f, funding_why = high / need, 'Grant covers part of the funding need'
        else:
            funding_f = 0.7
    return weighted([(55, sector_f, sector_why), (25, funding_f, funding_why), (20, urgency_f, urgency_why)])


# ── Papers ──────────────────────────────────────────────────────────────────

def score_paper(paper, startup):
    sector_f, sector_why = sector_fit(startup.get('sector'), paper.get('tags'))
    text_f, text_why = text_fit(startup_text(startup), f"{paper.get('title', '')} {paper.get('takeaway', '')}")
    return weighted([(70, sector_f, sector_why), (30, text_f, text_why)])
