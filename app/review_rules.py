"""Rules for admin review of ideas. Scores are calculated here, never in the browser."""

# criterion -> weight (weights add up to 1.0). Each criterion is scored 1 to 5.
CRITERIA = {
    'problem': 0.20,
    'innovation': 0.20,
    'feasibility': 0.20,
    'impact': 0.20,
    'team': 0.10,
    'alignment': 0.10,
}

DECISIONS = ('approved', 'rejected', 'revision_requested')

REJECT_CODES = (
    'duplicate', 'plagiarism', 'harmful_content', 'incomplete',
    'not_feasible', 'out_of_scope', 'low_impact', 'other',
)
# These reasons can reject an idea even when the score is not low.
HARD_REJECT_CODES = ('duplicate', 'plagiarism', 'harmful_content', 'incomplete')

APPROVE_MIN = 75
REVISION_MIN = 50
MIN_TEXT = 30  # minimum characters for comments and override justifications


def clean_scores(raw):
    """Return (scores, error). Every criterion must be a whole number from 1 to 5."""
    if not isinstance(raw, dict):
        return None, 'Scores are required'
    scores = {}
    for key in CRITERIA:
        value = raw.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            return None, 'Score for "%s" must be a whole number from 1 to 5' % key
        scores[key] = value
    return scores, None


def compute_total(scores):
    """Weighted total out of 100."""
    return round(sum(scores[k] / 5 * 100 * w for k, w in CRITERIA.items()))


def suggested_decision(total):
    if total >= APPROVE_MIN:
        return 'approved'
    if total >= REVISION_MIN:
        return 'revision_requested'
    return 'rejected'


def check_decision(decision, total, comment, reason_code=None, override=None):
    """Return an error message, or None if the decision is allowed."""
    comment = (comment or '').strip()
    override = (override or '').strip()

    if decision not in DECISIONS:
        return 'Decision must be one of: ' + ', '.join(DECISIONS)
    if len(comment) < MIN_TEXT:
        return 'A written reason of at least %d characters is required' % MIN_TEXT

    needs_override = False
    if decision == 'approved' and total < APPROVE_MIN:
        needs_override = True
    if decision == 'rejected':
        if reason_code not in REJECT_CODES:
            return 'A valid reject reason code is required'
        if total >= REVISION_MIN and reason_code not in HARD_REJECT_CODES:
            needs_override = True

    if needs_override and len(override) < MIN_TEXT:
        return ('This decision goes against the score. Add a justification '
                'of at least %d characters' % MIN_TEXT)
    return None
