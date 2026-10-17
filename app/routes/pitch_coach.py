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


# ---------------- Investor Arena ----------------
PERSONAS = {
    'vc': 'a skeptical venture capital investor who cares about market size, traction and returns',
    'grant': 'a Ministry grant officer who cares about national impact, feasibility, jobs and responsible use of public money',
    'mentor': 'an experienced startup mentor who probes weak assumptions and execution risks',
}
ROUNDS = 4
_sim = {}


def _sim_allowed(uid, limit=60):
    now = time.time()
    hits = [t for t in _sim.get(uid, []) if now - t < WINDOW]
    if len(hits) >= limit:
        _sim[uid] = hits
        return False
    hits.append(now)
    _sim[uid] = hits
    return True


def _chat(system, user, max_tokens):
    from groq import Groq
    resp = Groq(api_key=os.environ.get('GROQ_API_KEY'), timeout=45).chat.completions.create(
        model=MODEL, temperature=0.4, max_tokens=max_tokens,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    return resp.choices[0].message.content or ''


@pitch_bp.route('/arena', methods=['POST'])
@jwt_required()
def arena():
    d = request.get_json() or {}
    pitch = str(d.get('pitch', '')).strip()
    persona = PERSONAS.get(str(d.get('persona', 'vc')), PERSONAS['vc'])
    lang = LANGS.get(str(d.get('language', 'en')), 'English')
    action = d.get('action')
    hist = [h for h in (d.get('history') or []) if isinstance(h, dict)][:12]
    if len(pitch) < 80 or len(pitch) > 3000:
        return jsonify({'error': 'Pitch must be 80-3000 characters.'}), 400
    if not os.environ.get('GROQ_API_KEY'):
        return jsonify({'error': 'AI service is not configured'}), 503
    if not _sim_allowed(get_jwt_identity()):
        return jsonify({'error': 'Limit reached. Please try again later.'}), 429
    transcript = '\n'.join(
        ('INVESTOR: ' if h.get('role') == 'investor' else 'FOUNDER: ') + str(h.get('text', ''))[:800]
        for h in hist)
    base = f"STARTUP PITCH:\n{pitch}\n\nCONVERSATION SO FAR:\n{transcript or '(none yet)'}"
    try:
        if action == 'question':
            system = (f"You are {persona}. Ask exactly ONE sharp, specific question (max 30 words) "
                      "about the pitch or the founder's last answer. Do not repeat earlier topics. "
                      "Never invent facts about the startup. Reply with only the question, "
                      f"written in {lang}.")
            q = _chat(system, base, 200).strip().strip('"')
            return jsonify({'question': q[:400]}), 200
        if action == 'debrief':
            system = (f"You are {persona}, now giving feedback after the meeting. Judge ONLY what the "
                      "founder actually said. Reply with ONLY valid JSON: "
                      '{"verdict":"one honest sentence","scores":{"clarity":1-10,"evidence":1-10,'
                      '"confidence":1-10,"handling":1-10},"best_answer":"...","weakest_answer":"...",'
                      f'"next_steps":["...","...","..."]}}. Write text values in {lang}.')
            t = _chat(system, base, 1200)
            p = json.loads(t[t.index('{'): t.rindex('}') + 1])
            sc = {k: _score((p.get('scores') or {}).get(k)) for k in ('clarity', 'evidence', 'confidence', 'handling')}
            return jsonify({'verdict': str(p.get('verdict', ''))[:400], 'scores': sc,
                            'best_answer': str(p.get('best_answer', ''))[:500],
                            'weakest_answer': str(p.get('weakest_answer', ''))[:500],
                            'next_steps': _strs(p.get('next_steps'), 4)}), 200
    except Exception as exc:
        logger.warning('arena failed: %s', exc)
        return jsonify({'error': 'The AI could not respond. Please try again.'}), 502
    return jsonify({'error': 'Invalid action'}), 400
