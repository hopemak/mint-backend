"""
Enhanced Mentorship Output Service
Produces detailed mentorship plans
"""

from datetime import datetime, timedelta
from typing import Dict, List

class MentorshipOutputService:
    """Generates detailed mentorship outputs"""
    
    def __init__(self):
        self.mentorship_version = "2.0.0"
    
    def generate_mentorship_plan(self, startup_data: Dict, matched_mentors: List[Dict], score: float) -> Dict:
        """Generate complete mentorship plan"""
        
        return {
            "mentorship_metadata": {
                "plan_id": f"MP-{datetime.utcnow().strftime('%Y%m%d')}-{startup_data.get('startup_id', 'UNK')}",
                "generated_at": datetime.utcnow().isoformat(),
                "mentorship_version": self.mentorship_version,
                "duration_months": 12
            },
            "mentorship_summary": {
                "start_date": datetime.utcnow().strftime('%Y-%m-%d'),
                "end_date": (datetime.utcnow() + timedelta(days=365)).strftime('%Y-%m-%d'),
                "mentors_count": len(matched_mentors),
                "priority": "High" if score >= 70 else "Medium",
                "status": "Active"
            },
            "assigned_mentors": self._generate_mentor_details(matched_mentors, startup_data),
            "mentorship_goals": self._generate_mentorship_goals(startup_data, score),
            "quarterly_plan": self._generate_quarterly_plan(startup_data),
            "success_metrics": self._generate_success_metrics(startup_data),
            "resources": self._generate_resources(startup_data),
            "tracking_framework": self._generate_tracking_framework()
        }
    
    def _generate_mentor_details(self, mentors: List[Dict], startup_data: Dict) -> List[Dict]:
        details = []
        for i, mentor in enumerate(mentors[:2]):
            details.append({
                "mentor_id": mentor.get('mentor_id', f"M-{i+1:04d}"),
                "name": mentor.get('name', f"Mentor {i+1}"),
                "expertise": mentor.get('expertise', ['General']),
                "match_score": mentor.get('match_score', 85),
                "responsibilities": self._get_mentor_responsibilities(i),
                "meeting_schedule": {
                    "frequency": "Weekly" if i == 0 else "Bi-weekly",
                    "day": "Thursday" if i == 0 else "Monday",
                    "time": "10:00 AM" if i == 0 else "2:00 PM",
                    "duration": "60 minutes"
                },
                "contact": {
                    "email": f"{mentor.get('name', 'mentor').lower().replace(' ', '.')}@mentor.com",
                    "phone": "+254-XXX-XXX"
                },
                "introductory_session": {
                    "date": (datetime.utcnow() + timedelta(days=3)).strftime('%Y-%m-%d'),
                    "agenda": "Introduction, goal setting, action plan"
                }
            })
        return details
    
    def _get_mentor_responsibilities(self, index: int) -> List[str]:
        if index == 0:
            return [
                "Guide product development strategy",
                "Connect with research institutions",
                "Review technical approach",
                "Provide industry insights"
            ]
        else:
            return [
                "Guide business strategy",
                "Connect with investors",
                "Review financial planning",
                "Support growth planning"
            ]
    
    def _generate_mentorship_goals(self, startup_data: Dict, score: float) -> Dict:
        return {
            "quarter_1": {
                "goal": "Product Validation" if score >= 60 else "Product Development",
                "description": "Complete product-market fit validation",
                "metrics": ["100 farmer trials", "Product-market fit confirmed"],
                "key_activities": [
                    "Conduct customer discovery interviews",
                    "Refine product features",
                    "Complete validation trials"
                ]
            },
            "quarter_2": {
                "goal": "MVP Launch" if score >= 60 else "Prototype Development",
                "description": "Launch minimum viable product",
                "metrics": ["50 paying customers", "$50,000 revenue"],
                "key_activities": [
                    "Launch MVP",
                    "Onboard initial customers",
                    "Gather feedback and iterate"
                ]
            },
            "quarter_3": {
                "goal": "Revenue Growth",
                "description": "Achieve significant revenue growth",
                "metrics": ["200 customers", "$150,000 revenue"],
                "key_activities": [
                    "Scale customer acquisition",
                    "Refine pricing strategy",
                    "Build marketing engine"
                ]
            },
            "quarter_4": {
                "goal": "Scale Preparation",
                "description": "Prepare for scaling operations",
                "metrics": ["500 customers", "$500,000 revenue"],
                "key_activities": [
                    "Build operational processes",
                    "Prepare for funding round",
                    "Expand team"
                ]
            }
        }
    
    def _generate_quarterly_plan(self, startup_data: Dict) -> Dict:
        return {
            "quarter_1": {
                "focus": "Foundation Building",
                "topics": [
                    "Business model refinement",
                    "Customer development",
                    "Product roadmap finalization"
                ],
                "mentor_sessions": 12,
                "deliverables": ["Validated business model", "Detailed roadmap"]
            },
            "quarter_2": {
                "focus": "Product Development",
                "topics": [
                    "MVP development",
                    "Customer acquisition",
                    "Pricing strategy"
                ],
                "mentor_sessions": 10,
                "deliverables": ["Working MVP", "Initial customers"]
            },
            "quarter_3": {
                "focus": "Market Expansion",
                "topics": [
                    "Scaling operations",
                    "Team building",
                    "Investor relations"
                ],
                "mentor_sessions": 10,
                "deliverables": ["Scaled operations", "Investor pipeline"]
            },
            "quarter_4": {
                "focus": "Fundraising",
                "topics": [
                    "Series A preparation",
                    "Strategic partnerships",
                    "International expansion"
                ],
                "mentor_sessions": 8,
                "deliverables": ["Fundraising materials", "Partner agreements"]
            }
        }
    
    def _generate_success_metrics(self, startup_data: Dict) -> List[Dict]:
        return [
            {
                "metric": "Revenue Growth",
                "target": "100% QoQ",
                "frequency": "Monthly",
                "measurement": "Financial reports"
            },
            {
                "metric": "Customer Acquisition",
                "target": "20+ new customers/month",
                "frequency": "Monthly",
                "measurement": "CRM data"
            },
            {
                "metric": "Team Growth",
                "target": "2-3 new hires/quarter",
                "frequency": "Quarterly",
                "measurement": "HR reports"
            },
            {
                "metric": "Product Development",
                "target": "On-time milestone delivery",
                "frequency": "Monthly",
                "measurement": "Project management"
            }
        ]
    
    def _generate_resources(self, startup_data: Dict) -> Dict:
        return {
            "templates": [
                "Mentorship Meeting Agenda Template",
                "Progress Report Template",
                "Action Plan Template",
                "Strategy Review Template"
            ],
            "guides": [
                "How to Maximize Mentorship",
                "Setting SMART Goals Guide",
                "Effective Communication with Mentors",
                "Preparing for Funding Rounds"
            ],
            "tools": [
                "CRM System (discounted)",
                "Project Management Tool (free)",
                "Financial Modeling Templates",
                "Market Research Database"
            ],
            "contacts": [
                {
                    "name": "Dr. Sarah Mwangi",
                    "role": "Innovation Advisor",
                    "contact": "sarah.mwangi@mint.gov"
                },
                {
                    "name": "David Omondi",
                    "role": "Investment Director",
                    "contact": "david.omondi@mint.gov"
                }
            ]
        }
    
    def _generate_tracking_framework(self) -> Dict:
        return {
            "progress_reviews": {
                "frequency": "Monthly",
                "format": "Dashboard update",
                "participants": ["Founder", "Mentors", "Program Manager"]
            },
            "milestone_reviews": {
                "frequency": "Quarterly",
                "format": "Formal presentation",
                "participants": ["Founder", "Mentors", "Committee"]
            },
            "feedback_collection": {
                "frequency": "Monthly",
                "format": "Survey",
                "topics": ["Mentor effectiveness", "Progress", "Challenges"]
            }
        }
