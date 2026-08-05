"""
Unit Tests for Authentication
"""

import pytest
import json

class TestAuth:
    """Authentication endpoint tests"""
    
    def test_register_user(self, client):
        """Test user registration"""
        data = {
            'email': 'testuser@example.com',
            'password': 'test123',
            'full_name': 'Test User',
            'role': 'founder'
        }
        response = client.post('/api/auth/register', json=data)
        assert response.status_code in [200, 201]
        if response.status_code == 201:
            assert response.json.get('success') == True
    
    def test_register_duplicate_user(self, client):
        """Test duplicate user registration"""
        data = {
            'email': 'duplicate@example.com',
            'password': 'test123',
            'full_name': 'Duplicate User',
            'role': 'founder'
        }
        # First registration
        client.post('/api/auth/register', json=data)
        
        # Second registration
        response = client.post('/api/auth/register', json=data)
        # Should return error (409 Conflict)
        assert response.status_code in [409, 400]
    
    def test_login_user(self, client):
        """Test user login"""
        # Register first
        register_data = {
            'email': 'loginuser@example.com',
            'password': 'login123',
            'full_name': 'Login User',
            'role': 'founder'
        }
        client.post('/api/auth/register', json=register_data)
        
        # Login
        login_data = {
            'email': 'loginuser@example.com',
            'password': 'login123'
        }
        response = client.post('/api/auth/login', json=login_data)
        # Should succeed
        assert response.status_code in [200, 201]
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpass'
        }
        response = client.post('/api/auth/login', json=login_data)
        assert response.status_code in [401, 404]
    
    def test_missing_fields(self, client):
        """Test registration with missing fields"""
        data = {
            'email': 'missing@example.com'
        }
        response = client.post('/api/auth/register', json=data)
        assert response.status_code == 400
    
    def test_logout(self, client):
        """Test logout"""
        response = client.post('/api/auth/logout')
        assert response.status_code in [200, 201]
        if response.status_code == 200:
            assert response.json.get('success') == True
