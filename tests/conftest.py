"""
Pytest Configuration and Fixtures - MongoDB Disabled
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment BEFORE importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['MONGODB_URI'] = ''  # Disable MongoDB for tests

from app import create_app

@pytest.fixture
def app():
    """Create test app with in-memory storage only"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['MONGODB_URI'] = ''  # Disable MongoDB
    app.config['MONGODB_DB'] = 'mint_test'
    return app

@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    """Get authentication headers for a regular user"""
    # Register user
    register_data = {
        'email': 'testuser@example.com',
        'password': 'test123',
        'full_name': 'Test User',
        'role': 'founder'
    }
    client.post('/api/auth/register', json=register_data)
    
    # Login
    login_data = {
        'email': 'testuser@example.com',
        'password': 'test123'
    }
    response = client.post('/api/auth/login', json=login_data)
    
    # Get cookie
    cookie = response.headers.get('Set-Cookie', '')
    if cookie:
        cookie = cookie.split(';')[0]
        return {'Cookie': cookie}
    return {}

@pytest.fixture
def sample_startup_data():
    return {
        'business_name': 'Test Startup Inc',
        'sector': 'Technology',
        'description': 'A test startup',
        'employee_count': 5,
        'location': 'Central Region',
        'is_rural': False,
        'trl_level': 4,
        'has_prototype': True,
        'has_patent': False,
        'requested_funding': 100000
    }

@pytest.fixture
def sample_ml_data():
    return {
        'business_name': 'AI Health Solutions',
        'sector': 'Healthcare',
        'trl_level': 6,
        'employee_count': 8,
        'requested_funding': 500000,
        'innovation_score': 85,
        'market_potential': 78,
        'technical_feasibility': 80,
        'business_model': 72,
        'financial_plan': 70,
        'social_impact': 88,
        'team_capability': 82,
        'overall_risk': 28
    }

@pytest.fixture
def sample_funding_data():
    return {
        'startup_id': 'MINT-2024-0001',
        'amount': 100000,
        'purpose': 'Product Development',
        'stage': 'prototype'
    }
