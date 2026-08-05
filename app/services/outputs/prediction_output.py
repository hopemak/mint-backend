"""
Enhanced Prediction Output Service
Produces detailed startup success predictions
"""

from datetime import datetime
from typing import Dict, List
import numpy as np

class PredictionOutputService:
    """Generates detailed startup success predictions"""
    
    def __init__(self):
        self.prediction_version = "2.0.0"
    
    def generate_prediction_report(self, startup_data: Dict, ml_scores: Dict, probability: float) -> Dict:
        """Generate complete prediction report"""
        
        return {
            "prediction_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "prediction_version": self.prediction_version,
                "startup_id": startup_data.get('startup_id', 'Unknown'),
                "model_version": "v2.0.0"
            },
            "success_prediction": {
                "probability": round(probability * 100, 2),
                "confidence_interval": {
                    "lower": round(max(0, probability - 0.15) * 100, 2),
                    "upper": round(min(1, probability + 0.15) * 100, 2)
                },
                "confidence_level": "High" if probability > 0.7 else "Medium" if probability > 0.4 else "Low",
                "prediction_class": "SUCCESS" if probability > 0.5 else "FAILURE",
                "risk_level": self._get_risk_level(probability)
            },
            "detailed_forecast": self._generate_forecast(startup_data, probability),
            "key_success_factors": self._generate_success_factors(startup_data, ml_scores),
            "risk_factors": self._generate_risk_factors(startup_data, ml_scores, probability),
            "recommendations": self._generate_recommendations(startup_data, ml_scores, probability),
            "comparative_analysis": self._generate_comparative_analysis(startup_data, probability)
        }
    
    def _get_risk_level(self, probability: float) -> str:
        if probability >= 0.7:
            return "Low Risk"
        elif probability >= 0.5:
            return "Medium Risk"
        elif probability >= 0.3:
            return "High Risk"
        else:
            return "Very High Risk"
    
    def _generate_forecast(self, startup_data: Dict, probability: float) -> Dict:
        return {
            "revenue_forecast": {
                "year_1": "$250,000" if probability > 0.5 else "$100,000",
                "year_2": "$800,000" if probability > 0.5 else "$300,000",
                "year_3": "$2,500,000" if probability > 0.5 else "$800,000"
            },
            "growth_forecast": {
                "year_1": "100%" if probability > 0.5 else "50%",
                "year_2": "200%" if probability > 0.5 else "100%",
                "year_3": "150%" if probability > 0.5 else "80%"
            },
            "customer_forecast": {
                "year_1": "100" if probability > 0.5 else "50",
                "year_2": "500" if probability > 0.5 else "200",
                "year_3": "2,000" if probability > 0.5 else "800"
            },
            "team_forecast": {
                "year_1": "8" if probability > 0.5 else "5",
                "year_2": "15" if probability > 0.5 else "10",
                "year_3": "30" if probability > 0.5 else "20"
            },
            "funding_forecast": {
                "next_round": "Series A" if probability > 0.5 else "Seed",
                "amount_needed": "$2,000,000" if probability > 0.5 else "$500,000",
                "valuation_at_next_round": "$10,000,000" if probability > 0.5 else "$4,000,000"
            }
        }
    
    def _generate_success_factors(self, startup_data: Dict, ml_scores: Dict) -> List[Dict]:
        factors = []
        
        if ml_scores.get('innovation_score', 0) > 75:
            factors.append({
                "factor": "Strong Innovation",
                "score": ml_scores.get('innovation_score', 70),
                "impact": "High",
                "description": "The technology provides significant competitive advantage",
                "sustainability": "3-5 years"
            })
        
        if ml_scores.get('market_potential', 0) > 75:
            factors.append({
                "factor": "Large Market Opportunity",
                "score": ml_scores.get('market_potential', 70),
                "impact": "High",
                "description": "Growing market with clear customer demand",
                "sustainability": "5+ years"
            })
        
        if startup_data.get('team_capability', 0) > 75:
            factors.append({
                "factor": "Strong Team",
                "score": startup_data.get('team_capability', 70),
                "impact": "High",
                "description": "Experienced team with complementary skills",
                "sustainability": "Ongoing"
            })
        
        return factors
    
    def _generate_risk_factors(self, startup_data: Dict, ml_scores: Dict, probability: float) -> List[Dict]:
        risks = []
        
        if startup_data.get('trl_level', 0) < 5:
            risks.append({
                "risk": "Technology Immaturity",
                "level": "High",
                "impact": "Potential delays in product development",
                "mitigation": "Complete field validation, engage technical mentors"
            })
        
        if startup_data.get('employee_count', 0) < 3:
            risks.append({
                "risk": "Small Team",
                "level": "Medium",
                "impact": "Limited execution capacity",
                "mitigation": "Strategic hiring plan, use of contractors"
            })
        
        if probability < 0.5:
            risks.append({
                "risk": "Market Uncertainty",
                "level": "High",
                "impact": "Risk of product-market fit issues",
                "mitigation": "Conduct comprehensive market research"
            })
        
        return risks
    
    def _generate_recommendations(self, startup_data: Dict, ml_scores: Dict, probability: float) -> List[Dict]:
        recs = []
        
        if ml_scores.get('innovation_score', 0) < 70:
            recs.append({
                "priority": "High",
                "recommendation": "Strengthen innovation strategy",
                "action": "Conduct competitive analysis and patent landscaping",
                "timeline": "1-2 months"
            })
        
        if ml_scores.get('market_potential', 0) < 70:
            recs.append({
                "priority": "High",
                "recommendation": "Deepen market research",
                "action": "Conduct customer discovery interviews",
                "timeline": "1 month"
            })
        
        if startup_data.get('employee_count', 0) < 5:
            recs.append({
                "priority": "Medium",
                "recommendation": "Expand team",
                "action": "Hire key positions",
                "timeline": "3 months"
            })
        
        if probability < 0.5:
            recs.append({
                "priority": "Critical",
                "recommendation": "Pivot or refine business model",
                "action": "Re-evaluate product-market fit",
                "timeline": "Immediate"
            })
        
        return recs
    
    def _generate_comparative_analysis(self, startup_data: Dict, probability: float) -> Dict:
        return {
            "industry_benchmarks": {
                "success_rate": "42%",
                "average_time_to_profitability": "24 months",
                "average_funding_required": "$500,000"
            },
            "competitor_comparison": {
                "innovation_advantage": "High" if probability > 0.6 else "Medium",
                "market_advantage": "High" if probability > 0.6 else "Medium",
                "funding_advantage": "Medium" if probability > 0.5 else "Low"
            },
            "relative_positioning": {
                "overall_rank": "Top 20%" if probability > 0.7 else "Top 40%" if probability > 0.5 else "Bottom 40%",
                "peer_comparison": "Above average" if probability > 0.5 else "Below average",
                "recommended_action": "Proceed with confidence" if probability > 0.6 else "Proceed with caution"
            }
        }
