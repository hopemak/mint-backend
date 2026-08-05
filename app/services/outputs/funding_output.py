"""
Enhanced Funding Output Service
Produces detailed funding packages
"""

from datetime import datetime, timedelta
from typing import Dict, List

class FundingOutputService:
    """Generates detailed funding outputs"""
    
    def __init__(self):
        self.funding_version = "2.0.0"
    
    def generate_funding_package(self, startup_data: Dict, request_data: Dict, total_score: float) -> Dict:
        """Generate complete funding package"""
        
        approved_amount = self._calculate_approved_amount(request_data.get('amount', 0), total_score)
        
        return {
            "funding_metadata": {
                "package_id": f"FP-{datetime.utcnow().strftime('%Y%m%d')}-{startup_data.get('startup_id', 'UNK')}",
                "generated_at": datetime.utcnow().isoformat(),
                "funding_version": self.funding_version,
                "status": "Approved" if total_score >= 70 else "Under Review"
            },
            "funding_summary": {
                "requested_amount": request_data.get('amount', 0),
                "approved_amount": approved_amount,
                "approval_status": "Approved" if total_score >= 70 else "Conditional",
                "funding_type": "Grant + Equity" if total_score >= 80 else "Grant" if total_score >= 70 else "Conditional",
                "government_stake": self._calculate_government_stake(total_score)
            },
            "funding_breakdown": self._generate_funding_breakdown(approved_amount, total_score),
            "disbursement_schedule": self._generate_disbursement_schedule(approved_amount, total_score),
            "terms_and_conditions": self._generate_terms_conditions(total_score),
            "obligations": self._generate_obligations(startup_data, approved_amount),
            "milestones": self._generate_milestones(startup_data, approved_amount),
            "compliance_requirements": self._generate_compliance_requirements(startup_data)
        }
    
    def _calculate_approved_amount(self, requested: float, total_score: float) -> float:
        if total_score >= 85:
            return min(requested, 1000000)
        elif total_score >= 75:
            return min(requested * 0.8, 500000)
        elif total_score >= 65:
            return min(requested * 0.5, 250000)
        else:
            return 0
    
    def _calculate_government_stake(self, total_score: float) -> str:
        if total_score >= 85:
            return "15%"
        elif total_score >= 75:
            return "10%"
        else:
            return "5%"
    
    def _generate_funding_breakdown(self, amount: float, total_score: float) -> Dict:
        return {
            "grant_portion": amount * 0.25 if total_score >= 70 else 0,
            "equity_investment": amount * 0.75 if total_score >= 70 else amount,
            "convertible_note": 0,
            "total": amount,
            "government_contribution": amount * 0.15 if total_score >= 80 else amount * 0.10 if total_score >= 70 else 0,
            "private_investment": amount * 0.85 if total_score >= 80 else amount * 0.90 if total_score >= 70 else amount
        }
    
    def _generate_disbursement_schedule(self, amount: float, total_score: float) -> List[Dict]:
        schedule = [
            {
                "tranche": 1,
                "amount": amount * 0.30,
                "date": (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d'),
                "milestone": "Initial disbursement",
                "conditions": "Signed agreement"
            },
            {
                "tranche": 2,
                "amount": amount * 0.30,
                "date": (datetime.utcnow() + timedelta(days=90)).strftime('%Y-%m-%d'),
                "milestone": "Milestone 1 completed",
                "conditions": "Progress report approved"
            },
            {
                "tranche": 3,
                "amount": amount * 0.25,
                "date": (datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'),
                "milestone": "Milestone 2 completed",
                "conditions": "Milestone review passed"
            },
            {
                "tranche": 4,
                "amount": amount * 0.15,
                "date": (datetime.utcnow() + timedelta(days=270)).strftime('%Y-%m-%d'),
                "milestone": "Final disbursement",
                "conditions": "All conditions met"
            }
        ]
        return schedule
    
    def _generate_terms_conditions(self, total_score: float) -> Dict:
        return {
            "equity_stake": self._calculate_government_stake(total_score),
            "vesting_period": "3 years",
            "cliff_period": "1 year",
            "board_seat": "Observer" if total_score >= 75 else "No",
            "reporting_requirements": "Quarterly",
            "milestone_review": "Quarterly",
            "exit_terms": "Right of first refusal",
            "liquidation_preference": "1x non-participating"
        }
    
    def _generate_obligations(self, startup_data: Dict, amount: float) -> List[Dict]:
        return [
            {
                "obligation": "Use funds only for approved purposes",
                "deadline": "Immediate",
                "penalty": "Funds recall"
            },
            {
                "obligation": "Submit quarterly progress reports",
                "deadline": "Quarterly",
                "penalty": "Withholding of subsequent disbursements"
            },
            {
                "obligation": "Engage with assigned mentors",
                "deadline": "Monthly",
                "penalty": "Reduced support"
            },
            {
                "obligation": "Achieve approved milestones",
                "deadline": "Per milestone schedule",
                "penalty": "Review of funding"
            }
        ]
    
    def _generate_milestones(self, startup_data: Dict, amount: float) -> List[Dict]:
        return [
            {
                "milestone_id": "M1",
                "description": "Complete product development",
                "target_date": (datetime.utcnow() + timedelta(days=90)).strftime('%Y-%m-%d'),
                "success_criteria": "Working prototype demonstrated",
                "funding_release": amount * 0.30
            },
            {
                "milestone_id": "M2",
                "description": "Market validation",
                "target_date": (datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'),
                "success_criteria": "10 paying customers",
                "funding_release": amount * 0.25
            },
            {
                "milestone_id": "M3",
                "description": "Revenue generation",
                "target_date": (datetime.utcnow() + timedelta(days=270)).strftime('%Y-%m-%d'),
                "success_criteria": "$100,000 ARR",
                "funding_release": amount * 0.15
            }
        ]
    
    def _generate_compliance_requirements(self, startup_data: Dict) -> List[Dict]:
        return [
            {
                "requirement": "Regular financial reporting",
                "frequency": "Quarterly",
                "format": "Standardized template"
            },
            {
                "requirement": "Audit trail of expenditures",
                "frequency": "Continuous",
                "format": "Online system"
            },
            {
                "requirement": "Progress reporting",
                "frequency": "Monthly",
                "format": "Dashboard update"
            },
            {
                "requirement": "Mentor meeting logs",
                "frequency": "Monthly",
                "format": "Meeting summaries"
            }
        ]
