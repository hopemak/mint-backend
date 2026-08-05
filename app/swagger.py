"""
Swagger/OpenAPI Configuration
"""

from flasgger import Swagger, swag_from

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "MInT Innovation Platform API",
        "description": """
        ## 🏛️ MInT Innovation Management Platform API
        
        The MInT Innovation Platform is a comprehensive digital ecosystem for managing startup incubation, evaluation, funding, and commercialization.
        
        ### 🔐 Authentication
        This API uses JWT authentication. After login, the token is stored in cookies.
        
        ### 📋 Main Features
        - **User Management**: Register, login, role management
        - **Startup Management**: Create, update, track startups
        - **AI/ML Evaluation**: Get AI-powered startup evaluation
        - **Funding**: Request, approve, disburse funding
        - **Grants**: Apply for and manage grants
        - **Mentorship**: Match and manage mentors
        - **Dashboard**: Analytics and insights
        - **Audit**: Complete audit trail
        - **Email**: Automated notifications
        
        ### 🏛️ Ministry Use
        This platform is designed for the Ministry of Innovation & Technology to manage the complete innovation lifecycle.
        """,
        "version": "2.0.0",
        "contact": {
            "name": "MInT Support",
            "email": "support@mint.gov",
            "url": "https://mint.gov"
        },
        "license": {
            "name": "Proprietary - Ministry of Innovation & Technology",
            "url": "https://mint.gov/license"
        }
    },
    "basePath": "/api",
    "schemes": ["http", "https"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT token (format: Bearer <token>)"
        },
        "CookieAuth": {
            "type": "apiKey",
            "name": "access_token_cookie",
            "in": "cookie",
            "description": "JWT token stored in cookies"
        }
    },
    "security": [
        {"CookieAuth": []}
    ],
    "tags": [
        {"name": "Authentication", "description": "User authentication endpoints"},
        {"name": "Users", "description": "User management endpoints"},
        {"name": "Startups", "description": "Startup management endpoints"},
        {"name": "Funding", "description": "Funding request and management"},
        {"name": "Grants", "description": "Grant management endpoints"},
        {"name": "ML/AI", "description": "AI-powered evaluation and predictions"},
        {"name": "Mentors", "description": "Mentor management and matching"},
        {"name": "Dashboard", "description": "Analytics and insights"},
        {"name": "Documents", "description": "Document upload and management"},
        {"name": "Audit", "description": "Audit logging (Admin only)"}
    ],
    "definitions": {
        "User": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "example": "U-0001"},
                "email": {"type": "string", "example": "user@example.com"},
                "full_name": {"type": "string", "example": "John Doe"},
                "role": {"type": "string", "enum": ["admin", "founder", "mentor", "investor", "committee", "viewer"]},
                "status": {"type": "string", "enum": ["active", "inactive", "pending"]}
            }
        },
        "Startup": {
            "type": "object",
            "properties": {
                "startup_id": {"type": "string", "example": "MINT-2024-0042"},
                "business_name": {"type": "string", "example": "AgriTech Solutions"},
                "sector": {"type": "string", "example": "Agriculture"},
                "status": {"type": "string", "example": "under_review"},
                "trl_level": {"type": "integer", "example": 6},
                "requested_funding": {"type": "number", "example": 350000}
            }
        },
        "Evaluation": {
            "type": "object",
            "properties": {
                "overall_score": {"type": "number", "example": 87.6},
                "grade": {"type": "string", "example": "A"},
                "rating": {"type": "string", "example": "Excellent"},
                "innovation_score": {"type": "number", "example": 85},
                "market_potential": {"type": "number", "example": 78},
                "swot_analysis": {"type": "object"},
                "risk_assessment": {"type": "object"}
            }
        },
        "FundingRequest": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "example": "FR-0042"},
                "amount": {"type": "number", "example": 350000},
                "status": {"type": "string", "enum": ["pending", "approved", "rejected", "disbursed"]},
                "purpose": {"type": "string", "example": "Product Development"}
            }
        },
        "Grant": {
            "type": "object",
            "properties": {
                "grant_id": {"type": "string", "example": "G-0042"},
                "grant_name": {"type": "string", "example": "Innovation Seed Fund"},
                "max_amount": {"type": "number", "example": 50000},
                "deadline": {"type": "string", "example": "2024-06-30"}
            }
        },
        "Mentor": {
            "type": "object",
            "properties": {
                "mentor_id": {"type": "string", "example": "M-0042"},
                "full_name": {"type": "string", "example": "Dr. Elizabeth Wanjiku"},
                "expertise_areas": {"type": "array", "items": {"type": "string"}},
                "years_experience": {"type": "integer", "example": 20}
            }
        },
        "Error": {
            "type": "object",
            "properties": {
                "error": {"type": "string", "example": "Resource not found"},
                "code": {"type": "string", "example": "NOT_FOUND"},
                "status": {"type": "integer", "example": 404}
            }
        }
    }
}

def init_swagger(app):
    """Initialize Swagger documentation"""
    Swagger(
        app,
        config=swagger_config,
        template=swagger_template
    )
    return app
