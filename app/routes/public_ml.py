"""
Public ML Routes - No authentication required
Uses Groq API for real AI responses
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from groq import Groq
import json
import os

public_ml_bp = Blueprint('public_ml', __name__, url_prefix='/api/public')

# Initialize Groq client (key loaded from environment, never hardcoded)
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set in the environment (.env)")

client = Groq(api_key=GROQ_API_KEY)
MODEL = "openai/gpt-oss-120b"


def _get_rating(overall):
    if overall >= 85:
        return "Excellent"
    elif overall >= 70:
        return "Good"
    else:
        return "Average"


@public_ml_bp.route('/evaluate', methods=['POST', 'OPTIONS'])
@cross_origin(origins=["http://localhost:5173", "http://localhost:5174",
                        "http://localhost:5175", "http://localhost:5176", "*"])
def evaluate_public():
    """Public evaluation endpoint — uses Groq AI to generate real scores and SWOT."""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.json or {}
        title       = data.get('title', 'Unnamed Idea')
        description = data.get('description', '')
        category    = data.get('category', 'General')
        industry    = data.get('industry', 'Technology')
        target_mkt  = data.get('target_market', '')
        biz_model   = data.get('business_model', '')

        # Self-assessment inputs (used as context / hints for the AI, not averaged)
        innovation_hint  = int(data.get('innovation_score', 70))
        market_hint      = int(data.get('market_potential', 70))
        feasibility_hint = int(data.get('feasibility', 70))
        financial_hint   = int(data.get('financial_plan', 70))
        social_hint      = int(data.get('social_impact', 70))
        team_hint        = int(data.get('team_capability', 70))

        print(f"📥 Evaluating: {title}")

        # ── Ask Groq to evaluate the idea and return structured JSON ──────────
        prompt = f"""You are an expert startup evaluator for the MInT Innovation Incubator in Ethiopia.
Carefully evaluate the following startup idea and return ONLY a valid JSON object — no markdown, no explanation, no extra text.

IDEA DETAILS:
Title: {title}
Description: {description}
Category: {category}
Industry: {industry}
Target Market: {target_mkt}
Business Model: {biz_model}

FOUNDER SELF-ASSESSMENT (use as additional context, not final scores):
Innovation: {innovation_hint}/100 | Market Potential: {market_hint}/100 | Feasibility: {feasibility_hint}/100
Financial Plan: {financial_hint}/100 | Social Impact: {social_hint}/100 | Team Capability: {team_hint}/100

Return this exact JSON structure with no other text:
{{
  "innovation_score": <integer 0-100 based on your evaluation>,
  "market_potential": <integer 0-100>,
  "feasibility": <integer 0-100>,
  "financial_plan": <integer 0-100>,
  "social_impact": <integer 0-100>,
  "team_capability": <integer 0-100>,
  "swot": {{
    "strengths": ["<specific strength 1>", "<specific strength 2>", "<specific strength 3>"],
    "weaknesses": ["<specific weakness 1>", "<specific weakness 2>", "<specific weakness 3>"],
    "opportunities": ["<specific opportunity 1>", "<specific opportunity 2>", "<specific opportunity 3>"],
    "threats": ["<specific threat 1>", "<specific threat 2>", "<specific threat 3>"]
  }},
  "feedback": "<one personalized sentence of advice for this specific idea>"
}}"""

        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )

        raw = completion.choices[0].message.content.strip()

        # Strip markdown code fences if the model wraps the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        ai = json.loads(raw)

        innovation  = max(0, min(100, int(ai.get('innovation_score', innovation_hint))))
        market      = max(0, min(100, int(ai.get('market_potential', market_hint))))
        feasibility = max(0, min(100, int(ai.get('feasibility', feasibility_hint))))
        financial   = max(0, min(100, int(ai.get('financial_plan', financial_hint))))
        social      = max(0, min(100, int(ai.get('social_impact', social_hint))))
        team        = max(0, min(100, int(ai.get('team_capability', team_hint))))

        overall          = int((innovation + market + feasibility + financial + social + team) / 6)
        technical_cmplx  = int((innovation + feasibility) / 2)
        financial_viab   = int((financial + market) / 2)
        risk_score       = 100 - overall
        rating           = _get_rating(overall)
        approval_status  = 'Approved' if overall >= 70 else 'Under Review'

        swot = ai.get('swot', {
            'strengths':     ['Strong technical concept', 'Clear target market', 'Innovative approach'],
            'weaknesses':    ['Limited resources', 'Market competition', 'Regulatory challenges'],
            'opportunities': ['Growing market demand', 'Partnership potential', 'Technology trends'],
            'threats':       ['Economic uncertainty', 'New competitors', 'Regulatory changes'],
        })
        feedback_text = ai.get('feedback', 'Keep refining your idea and gather user feedback.')

        response = {
            'success': True,
            'data': {
                'overall_score':       overall,
                'rating':              rating,
                'innovation_score':    innovation,
                'market_potential':    market,
                'feasibility':         feasibility,
                'financial_plan':      financial,
                'social_impact':       social,
                'team_capability':     team,
                'technical_complexity': technical_cmplx,
                'financial_viability': financial_viab,
                'risk_score':          risk_score,
                'approval_status':     approval_status,
                'swot_analysis':       swot,
                'feedback': [
                    feedback_text,
                    f'📊 Overall score: {overall}/100 — {rating}.',
                    '💡 Ask me anything about your evaluation below.',
                ],
            },
        }

        print(f"✅ AI Evaluation complete: {overall}% ({rating})")
        return jsonify(response)

    except json.JSONDecodeError as e:
        print(f"⚠ JSON parse error from Groq, falling back to hint-based scores: {e}")
        # Graceful fallback: use the user's self-assessment hints so the page still works
        innovation  = innovation_hint
        market      = market_hint
        feasibility = feasibility_hint
        financial   = financial_hint
        social      = social_hint
        team        = team_hint
        overall     = int((innovation + market + feasibility + financial + social + team) / 6)
        return jsonify({
            'success': True,
            'data': {
                'overall_score':       overall,
                'rating':              _get_rating(overall),
                'innovation_score':    innovation,
                'market_potential':    market,
                'feasibility':         feasibility,
                'financial_plan':      financial,
                'social_impact':       social,
                'team_capability':     team,
                'technical_complexity': int((innovation + feasibility) / 2),
                'financial_viability': int((financial + market) / 2),
                'risk_score':          100 - overall,
                'approval_status':     'Approved' if overall >= 70 else 'Under Review',
                'swot_analysis': {
                    'strengths':     ['Strong technical concept', 'Clear target market', 'Innovative approach'],
                    'weaknesses':    ['Limited resources', 'Market competition', 'Regulatory challenges'],
                    'opportunities': ['Growing market demand', 'Partnership potential', 'Technology trends'],
                    'threats':       ['Economic uncertainty', 'New competitors', 'Regulatory changes'],
                },
                'feedback': ['Keep refining your idea based on user feedback.',
                             '💡 Ask me anything about your evaluation below.'],
            },
        })

    except Exception as e:
        print(f"❌ Evaluation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@public_ml_bp.route('/chat', methods=['POST', 'OPTIONS'])
@cross_origin(origins=["http://localhost:5173", "http://localhost:5174",
                        "http://localhost:5175", "http://localhost:5176", "*"])
def chat_public():
    """Public chat endpoint - NO AUTH required - Uses Groq AI"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data    = request.json or {}
        message = data.get('message', '')
        context = data.get('context', {})

        print(f"💬 Public Chat: {message}")

        # Build context string
        context_parts = []
        if context.get('title'):
            context_parts.append(f"Startup idea: {context['title']}")
        if context.get('overallScore'):
            context_parts.append(f"Overall score: {context['overallScore']}/100")
        if context.get('rating'):
            context_parts.append(f"Rating: {context['rating']}")
        if context.get('scores') and isinstance(context['scores'], dict):
            score_lines = ", ".join(
                f"{k.replace('_', ' ').title()}: {v}/100"
                for k, v in context['scores'].items()
            )
            context_parts.append(f"Dimension scores — {score_lines}")
        context_msg = " | ".join(context_parts)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert AI startup advisor for the MInT Innovation Incubator in Ethiopia. "
                    "Your role is to help founders understand their AI evaluation results and provide "
                    "specific, actionable advice to improve their scores and build a stronger startup. "
                    "Be encouraging but honest. Keep responses concise (2-3 short paragraphs). "
                    "Always reference the user's specific context and scores when available."
                ),
            }
        ]

        if context_msg:
            messages.append({
                "role": "system",
                "content": f"Evaluation context for this conversation: {context_msg}",
            })

        messages.append({"role": "user", "content": message})

        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            top_p=0.9,
        )

        reply = completion.choices[0].message.content
        print(f"✅ Chat response: {reply[:80]}...")

        return jsonify({'success': True, 'data': {'reply': reply}})

    except Exception as e:
        print(f"❌ Chat error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {'reply': f"I'm having trouble right now. Please try again in a moment."},
        }), 500
