"""Unit tests for the rule-based matching (pure functions, no Flask needed)."""
from datetime import datetime

from app.utils.matching import (
    sector_fit, text_fit, weighted, score_mentor, score_investor, score_grant, score_paper, grant_is_open,
)

TODAY = datetime(2026, 10, 28)


def test_same_sector_ignores_case_and_spelling():
    assert sector_fit('FinTech', ['Fintech'])[0] == 1.0
    assert sector_fit('AgriTech', ['Agriculture'])[0] == 1.0


def test_generic_tech_is_only_a_partial_match():
    # The old rule gave a full match because "Tech" is inside "AgriTech".
    assert sector_fit('AgriTech', ['Tech', 'SaaS'])[0] == 0.5
    assert sector_fit('AgriTech', ['FinTech'])[0] == 0.0


def test_unknown_data_is_skipped_not_punished():
    assert sector_fit('', ['Tech'])[0] is None
    assert weighted([(40, None, None), (60, 1.0, 'ok')])[0] == 100


def test_score_is_between_0_and_100():
    mentor = {'preferred_sectors': ['AgriTech'], 'expertise_areas': 'Agriculture', 'years_experience': 30, 'rating': 9, 'availability': 'available'}
    score, _ = score_mentor(mentor, {'sector': 'AgriTech'})
    assert 0 <= score <= 100


def test_available_mentor_beats_busy_mentor_with_same_profile():
    base = {'preferred_sectors': ['HealthTech'], 'expertise_areas': 'Health', 'years_experience': 10, 'rating': 4.5}
    startup = {'sector': 'HealthTech'}
    assert score_mentor({**base, 'availability': 'available'}, startup)[0] > score_mentor({**base, 'availability': 'busy'}, startup)[0]


def test_matching_sector_beats_non_matching_sector():
    agri = {'preferred_sectors': ['Agriculture'], 'years_experience': 5}
    fin = {'preferred_sectors': ['Fintech'], 'years_experience': 5}
    s = {'sector': 'AgriTech'}
    assert score_mentor(agri, s)[0] > score_mentor(fin, s)[0]


def test_expired_grants_are_not_open():
    assert not grant_is_open({'deadline': '2026-09-10'}, TODAY)
    assert grant_is_open({'deadline': '2026-11-15'}, TODAY)
    assert not grant_is_open({'deadline': '2027-01-01', 'status': 'closed'}, TODAY)


def test_stage_words_in_grant_sectors_are_ignored():
    grant = {'sectors': ['Seed Stage'], 'deadline': '2026-11-15'}
    score, _ = score_grant(grant, {'sector': 'AgriTech'}, TODAY)
    assert score > 0  # only the deadline factor is measurable, nothing is punished


def test_investor_stage_fit_uses_trl():
    seed = {'preferred_sectors': ['Tech'], 'investment_stage': 'Seed'}
    series_b = {'preferred_sectors': ['Tech'], 'investment_stage': 'Series B'}
    startup = {'sector': 'Tech', 'trl': '6'}
    assert score_investor(seed, startup)[0] > score_investor(series_b, startup)[0]


def test_paper_uses_sector_tags():
    assert score_paper({'tags': ['Tech', 'AI'], 'title': 'x', 'takeaway': 'y'}, {'sector': 'Tech'})[0] > \
           score_paper({'tags': ['Education'], 'title': 'x', 'takeaway': 'y'}, {'sector': 'Tech'})[0]
