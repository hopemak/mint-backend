from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import os

app = Flask(__name__)

# ✅ FIX: Allow all origins with credentials
CORS(app, 
     supports_credentials=True,
     origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health():
    return jsonify({'status': 'OK', 'message': 'Backend is running!'})

@app.route('/api/ml/evaluate', methods=['POST', 'OPTIONS'])
def evaluate():
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.json
    print(f"📥 Evaluating: {data.get('title', 'Unknown')}")
    
    # Use input scores or generate realistic ones
    innovation = data.get('innovation_score', random.randint(60, 95))
    market = data.get('market_potential', random.randint(60, 95))
    feasibility = data.get('feasibility', random.randint(60, 95))
    financial = data.get('financial_plan', random.randint(60, 95))
    social = data.get('social_impact', random.randint(60, 95))
    team = data.get('team_capability', random.randint(60, 95))
    
    # Calculate overall
    overall = int((innovation + market + feasibility + financial + social + team) / 6)
    
    # Generate rating
    if overall >= 85:
        rating = "Excellent"
    elif overall >= 70:
        rating = "Good"
    elif overall >= 50:
        rating = "Average"
    else:
        rating = "Needs Improvement"
    
    # Generate risk
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

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
