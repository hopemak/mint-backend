"""AI Pitch Coach (founders). Uses Groq, same key as the public AI routes."""
import json
import logging
import os
import time
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

logger = logging.getLogger(__name__)
pitch_bp = Blueprint('pitch', __name__, url_prefix='/api/pitch')

MODEL = "openai/gpt-oss-120b"
LANGS = {'en': 'English', 'am': 'Amharic', 'om': 'Afaan Oromo'}
LIMIT, WINDOW = 10, 3600
_recent = {}


def _allowed(uid):
    now = time.time()
    hits = [t for t in _recent.get(uid, []) if now - t < WINDOW]
    if len(hits) >= LIMIT:
        _recent[uid] = hits
        return False
    hits.append(now)
    _recent[uid] = hits
    return True


def _score(v):
    try:
        return max(1, min(10, int(round(float(v)))))
    except (TypeError, ValueError):
        return 0


def _strs(v, n=5):
    return [str(x)[:300] for x in v][:n] if isinstance(v, list) else []


@pitch_bp.route('/coach', methods=['POST'])
@jwt_required()
def coach():
    data = request.get_json() or {}
    pitch = str(data.get('pitch', '')).strip()
    lang = LANGS.get(str(data.get('language', 'en')), 'English')
    if len(pitch) < 80:
        return jsonify({'error': 'Please write at least a few sentences (80+ characters).'}), 400
    if len(pitch) > 3000:
        return jsonify({'error': 'Pitch is too long (max 3000 characters).'}), 400
    if not _allowed(get_jwt_identity()):
        return jsonify({'error': 'Limit reached (10 per hour). Please try again later.'}), 429

    key = os.environ.get('GROQ_API_KEY')
    if not key:
        return jsonify({'error': 'AI service is not configured'}), 503

    system = (
        "You are a strict but supportive startup pitch coach for Ethiopian founders. "
        "Evaluate ONLY what is written. Never invent facts, numbers, customers or traction. "
        "If something is missing, say it is missing. The rewrite must use only facts from the pitch "
        "and keep it under 150 words. Reply with ONLY valid JSON, no markdown, in this shape: "
        '{"scores":{"problem":{"score":1-10,"comment":"..."},"market":{...},"solution":{...},"team":{...}},'
        '"strengths":["..."],"improvements":["..."],"rewrite":"..."}. '
        f"Write all text values in {lang}."
    )
    try:
        from groq import Groq
        resp = Groq(api_key=key, timeout=45).chat.completions.create(
            model=MODEL, temperature=0.3, max_tokens=1800,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": pitch}],
        )
        text = resp.choices[0].message.content or ''
        parsed = json.loads(text[text.index('{'): text.rindex('}') + 1])
    except Exception as exc:
        logger.warning('pitch coach failed: %s', exc)
        return jsonify({'error': 'The AI could not analyse this pitch. Please try again.'}), 502

    scores = {}
    for k in ('problem', 'market', 'solution', 'team'):
        item = (parsed.get('scores') or {}).get(k) or {}
        scores[k] = {'score': _score(item.get('score')), 'comment': str(item.get('comment', ''))[:400]}
    return jsonify({
        'scores': scores,
        'strengths': _strs(parsed.get('strengths')),
        'improvements': _strs(parsed.get('improvements')),
        'rewrite': str(parsed.get('rewrite', ''))[:1500],
    }), 200
