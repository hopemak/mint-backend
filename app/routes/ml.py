"""
ML Endpoints - Integrates with trained models
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
import pickle
import json
import numpy as np
import os
from datetime import datetime

ml_bp = Blueprint('ml', __name__)

# Load ML models
MODEL_DIR = './company_models'

def load_models():
    try:
        with open(f'{MODEL_DIR}/model.pkl', 'rb') as f:
            model = pickle.load(f)
        with open(f'{MODEL_DIR}/scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)
        with open(f'{MODEL_DIR}/feature_names.json', 'r') as f:
            feature_names = json.load(f)
        with open(f'{MODEL_DIR}/metrics.json', 'r') as f:
            metrics = json.load(f)
        return model, scaler, feature_names, metrics
    except Exception as e:
        current_app.logger.error(f"Error loading models: {e}")
        return None, None, None, None

model, scaler, feature_names, metrics = load_models()

def prepare_features(data):
    features = [
        float(data.get('trl_level', 4)),
        float(data.get('employee_count', 3)),
        float(data.get('is_rural', 0)),
        float(data.get('has_prototype', 0)),
        float(data.get('has_patent', 0)),
        float(data.get('patent_count', 0)),
        float(data.get('requested_funding', 100000)) / 100000,
        float(data.get('private_funding', 0)) / 100000,
        float(data.get('founder_experience', 5)),
        float(data.get('founder_previous_startups', 0)),
        float(data.get('founder_leadership', 70)),
        float(data.get('founder_tech_skill', 70)),
        float(data.get('founder_business_skill', 70)),
        float(data.get('innovation_score', 70)),
        float(data.get('market_potential', 70)),
        float(data.get('technical_feasibility', 70)),
        float(data.get('business_model', 70)),
        float(data.get('financial_plan', 70)),
        float(data.get('social_impact', 70)),
        float(data.get('team_capability', 70)),
        float(data.get('overall_risk', 40))
    ]
    return features

@ml_bp.route('/evaluate', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['ML/AI'],
    'summary': 'Evaluate a startup idea',
    'description': 'Get AI-powered evaluation of a startup idea with scores, SWOT, and recommendations.',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'business_name': {'type': 'string', 'example': 'AgriTech Solutions'},
                    'sector': {'type': 'string', 'example': 'Agriculture'},
                    'trl_level': {'type': 'integer', 'example': 6},
                    'employee_count': {'type': 'integer', 'example': 8},
                    'requested_funding': {'type': 'number', 'example': 350000},
                    'innovation_score': {'type': 'number', 'example': 85},
                    'market_potential': {'type': 'number', 'example': 78},
                    'technical_feasibility': {'type': 'number', 'example': 80},
                    'business_model': {'type': 'number', 'example': 72},
                    'financial_plan': {'type': 'number', 'example': 70},
                    'social_impact': {'type': 'number', 'example': 88},
                    'team_capability': {'type': 'number', 'example': 82},
                    'overall_risk': {'type': 'number', 'example': 28}
                },
                'required': ['business_name', 'sector']
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Evaluation complete',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': True},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'overall_score': {'type': 'number', 'example': 87.6},
                            'grade': {'type': 'string', 'example': 'A'},
                            'rating': {'type': 'string', 'example': 'Excellent'},
                            'swot_analysis': {'type': 'object'},
                            'risk_assessment': {'type': 'object'}
                        }
                    }
                }
            }
        },
        '400': {'description': 'Bad request'},
        '401': {'description': 'Unauthorized'},
        '500': {'description': 'Server error'}
    }
})
def evaluate_idea():
    """Evaluate an idea using ML model"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        features = prepare_features(data)
        features_array = np.array(features).reshape(1, -1)
        features_scaled = scaler.transform(features_array)
        
        prediction = model.predict(features_scaled)[0]
        probability = model.predict_proba(features_scaled)[0, 1]
        
        importance = dict(zip(feature_names, model.feature_importances_))
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
        
        result = {
            'overall_score': round(probability * 100, 2),
            'prediction': 'SUCCESS' if prediction == 1 else 'FAILURE',
            'confidence': round(probability * 100, 2),
            'status': get_status(probability),
            'top_factors': [{'name': name, 'importance': round(imp * 100, 2)} for name, imp in top_features],
            'swot_analysis': generate_swot(data),
            'scores': {
                'innovation': data.get('innovation_score', 70),
                'market_potential': data.get('market_potential', 70),
                'technical_feasibility': data.get('technical_feasibility', 70),
                'business_model': data.get('business_model', 70),
                'financial_plan': data.get('financial_plan', 70),
                'social_impact': data.get('social_impact', 70),
                'team_capability': data.get('team_capability', 70)
            },
            'risk_score': data.get('overall_risk', 40),
            'model_version': 'v2.0.0',
            'evaluation_time': datetime.utcnow().isoformat()
        }
        
        return jsonify({'success': True, 'data': result}), 200
        
    except Exception as e:
        current_app.logger.error(f"Evaluation error: {e}")
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/predict', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['ML/AI'],
    'summary': 'Predict startup success',
    'description': 'Get AI-powered success prediction for a startup.',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'innovation_score': {'type': 'number', 'example': 85},
                    'market_potential': {'type': 'number', 'example': 78},
                    'technical_feasibility': {'type': 'number', 'example': 80},
                    'business_model': {'type': 'number', 'example': 72},
                    'financial_plan': {'type': 'number', 'example': 70},
                    'social_impact': {'type': 'number', 'example': 88},
                    'team_capability': {'type': 'number', 'example': 82},
                    'overall_risk': {'type': 'number', 'example': 28}
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Prediction complete',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': True},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'success_probability': {'type': 'number', 'example': 76.3},
                            'prediction': {'type': 'string', 'example': 'SUCCESS'},
                            'risk_level': {'type': 'string', 'example': 'Low Risk'}
                        }
                    }
                }
            }
        }
    }
})
def predict_success():
    """Predict startup success"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        features = prepare_features(data)
        features_array = np.array(features).reshape(1, -1)
        features_scaled = scaler.transform(features_array)
        
        prediction = model.predict(features_scaled)[0]
        probability = model.predict_proba(features_scaled)[0, 1]
        
        importance = dict(zip(feature_names, model.feature_importances_))
        top_factors = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
        
        result = {
            'success_probability': round(probability * 100, 2),
            'prediction': 'SUCCESS' if prediction == 1 else 'FAILURE',
            'key_factors': [
                {'factor': name, 'impact': 'positive' if imp > 0.05 else 'moderate', 'importance': round(imp * 100, 2)}
                for name, imp in top_factors
            ],
            'recommendations': generate_recommendations(data, probability),
            'risk_level': get_risk_level(probability),
            'model_version': 'v2.0.0'
        }
        
        return jsonify({'success': True, 'data': result}), 200
        
    except Exception as e:
        current_app.logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/metrics', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['ML/AI'],
    'summary': 'Get model metrics',
    'description': 'Get ML model performance metrics.',
    'responses': {
        '200': {
            'description': 'Metrics retrieved',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': True},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'accuracy': {'type': 'number', 'example': 76.3},
                            'precision': {'type': 'number', 'example': 65.86},
                            'recall': {'type': 'number', 'example': 51.9},
                            'f1': {'type': 'number', 'example': 58.05},
                            'auc_roc': {'type': 'number', 'example': 77.79}
                        }
                    }
                }
            }
        }
    }
})
def get_metrics():
    """Get model performance metrics"""
    return jsonify({
        'success': True,
        'data': {
            'accuracy': metrics.get('metrics', {}).get('accuracy', 0) * 100,
            'precision': metrics.get('metrics', {}).get('precision', 0) * 100,
            'recall': metrics.get('metrics', {}).get('recall', 0) * 100,
            'f1': metrics.get('metrics', {}).get('f1', 0) * 100,
            'auc_roc': metrics.get('metrics', {}).get('auc_roc', 0) * 100,
            'cv_score': metrics.get('cv_score', 0) * 100,
            'oob_score': metrics.get('oob_score', 0) * 100
        }
    }), 200

# ... (rest of the ML functions: generate_swot, get_status, get_risk_level, generate_recommendations)
def generate_swot(data):
    return {
        'strengths': [
            'Strong innovation potential' if data.get('innovation_score', 70) > 75 else 'Innovation needs improvement',
            'Good market opportunity' if data.get('market_potential', 70) > 75 else 'Market needs research',
            'Feasible implementation' if data.get('technical_feasibility', 70) > 75 else 'Feasibility needs assessment'
        ],
        'weaknesses': [
            'Complex implementation' if data.get('technical_feasibility', 70) > 70 else 'Technical approach is clear',
            'Competitive market' if data.get('market_potential', 70) < 50 else 'Good market positioning'
        ],
        'opportunities': [
            'Growing market demand',
            'Partnership opportunities',
            'Innovation ecosystem support'
        ],
        'threats': [
            'Regulatory changes' if data.get('overall_risk', 40) > 60 else 'Low regulatory risk',
            'Competitor activity' if data.get('market_potential', 70) < 50 else 'Competitor landscape manageable'
        ]
    }

def get_status(probability):
    if probability >= 0.85:
        return {'label': 'Excellent', 'color': 'green', 'icon': '✅'}
    elif probability >= 0.70:
        return {'label': 'Good', 'color': 'blue', 'icon': '📈'}
    elif probability >= 0.50:
        return {'label': 'Moderate', 'color': 'orange', 'icon': '⚠️'}
    else:
        return {'label': 'Needs Work', 'color': 'red', 'icon': '❌'}

def get_risk_level(probability):
    if probability >= 0.70:
        return 'Low Risk'
    elif probability >= 0.50:
        return 'Medium Risk'
    elif probability >= 0.30:
        return 'High Risk'
    else:
        return 'Very High Risk'

def generate_recommendations(data, probability):
    recs = []
    if data.get('innovation_score', 70) < 60:
        recs.append("Enhance innovation by researching existing solutions")
    if data.get('market_potential', 70) < 60:
        recs.append("Conduct deeper market research")
    if data.get('technical_feasibility', 70) < 60:
        recs.append("Develop a more detailed implementation plan")
    if data.get('financial_plan', 70) < 60:
        recs.append("Refine financial projections")
    if probability > 0.70:
        recs.append("Consider aggressive market expansion")
    elif probability < 0.30:
        recs.append("Re-evaluate business model")
    return recs[:4] if recs else ["Focus on customer acquisition", "Optimize operational efficiency"]
