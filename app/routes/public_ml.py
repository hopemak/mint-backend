"""
Public ML Routes - No authentication required
Uses Groq API for real AI responses
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from groq import Groq
import random
import os

public_ml_bp = Blueprint('public_ml', __name__, url_prefix='/api/public')

# Initialize Groq client
client = Groq(
    api_key="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"
)
MODEL = "llama-3.3-70b-versatile"

@public_ml_bp.route('/evaluate', methods=['POST', 'OPTIONS'])
@cross_origin(origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "*"])
def evaluate_public():
    """Public evaluation endpoint - NO AUTH required"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.json
        print(f"📥 Public Evaluation: {data.get('title', 'Unknown')}")
        
        # Extract scores
        innovation = int(data.get('innovation_score', random.randint(60, 95)))
        market = int(data.get('market_potential', random.randint(60, 95)))
        feasibility = int(data.get('feasibility', random.randint(60, 95)))
        financial = int(data.get('financial_plan', random.randint(60, 95)))
        social = int(data.get('social_impact', random.randint(60, 95)))
        team = int(data.get('team_capability', random.randint(60, 95)))
        
        # Calculate overall
        overall = int((innovation + market + feasibility + financial + social + team) / 6)
        
        # Generate rating
        if overall >= 85:
            rating = "Excellent"
        elif overall >= 70:
            rating = "Good"
        else:
            rating = "Average"
        
        risk = 100 - overall
        
        response = {
            'success': True,
            'data': {
                'overall_score': overall,
                'rating': rating,
                'innovation_score': innovation,
                'market_potential': market,
                'feasibility': feasibility,
                'financial_plan': financial,
                'social_impact': social,
                'team_capability': team,
                'technical_complexity': int((innovation + feasibility) / 2),
                'financial_viability': int((financial + market) / 2),
                'risk_score': risk,
                'approval_status': 'Approved' if overall >= 70 else 'Under Review',
                'swot_analysis': {
                    'strengths': ['Strong technical team', 'Clear market need', 'Innovative solution'],
                    'weaknesses': ['Limited resources', 'Market competition', 'Regulatory challenges'],
                    'opportunities': ['Growing market', 'Partnership potential', 'Technology trends'],
                    'threats': ['Economic uncertainty', 'New competitors', 'Regulatory changes']
                },
                'feedback': [
                    '🌟 Your idea shows strong potential!',
                    '💡 Consider refining your go-to-market strategy.',
                    '📈 Great social impact potential.'
                ]
            }
        }
        
        print(f"✅ Evaluation complete: {overall}%")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@public_ml_bp.route('/chat', methods=['POST', 'OPTIONS'])
@cross_origin(origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "*"])
def chat_public():
    """Public chat endpoint - NO AUTH required - Uses Groq AI"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.json
        message = data.get('message', '')
        context = data.get('context', {})
        
        print(f"💬 Public Chat: {message}")
        print(f"📋 Context: {context}")
        
        # Build context message
        context_msg = ""
        if context:
            parts = []
            if context.get('title'):
                parts.append(f"Idea: {context['title']}")
            if context.get('overallScore'):
                parts.append(f"Score: {context['overallScore']}%")
            if context.get('scores') and isinstance(context['scores'], dict):
                score_text = ", ".join([f"{k}: {v}%" for k, v in context['scores'].items()])
                parts.append(f"Scores: {score_text}")
            context_msg = " | ".join(parts)
        
        # Build messages for Groq
        messages = [
            {
                "role": "system",
                "content": """You are an AI assistant for the Innovation Incubator Platform. 
Your role is to help entrepreneurs understand their evaluation scores and provide actionable advice.
Be helpful, specific, and encouraging. Keep responses concise (2-3 paragraphs).
Always refer to the user's specific scores and context when available.
If you don't know something, say so honestly."""
            }
        ]
        
        if context_msg:
            messages.append({
                "role": "system",
                "content": f"Current evaluation context: {context_msg}"
            })
        
        messages.append({"role": "user", "content": message})
        
        # ✅ Call Groq API
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            top_p=0.9
        )
        
        reply = completion.choices[0].message.content
        print(f"✅ Groq Response: {reply[:100]}...")
        
        return jsonify({
            'success': True,
            'data': {'reply': reply}
        })
        
    except Exception as e:
        print(f"❌ Chat Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {'reply': f"Error: {str(e)}"}
        }), 500
