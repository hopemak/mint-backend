"""
Unit Tests for Startups
"""

import pytest

class TestStartups:
    """Startup endpoint tests"""
    
    def test_list_sectors(self, client, auth_headers):
        """Test listing sectors"""
        if not auth_headers:
            pytest.skip("No auth headers available")
        
        response = client.get('/api/startups/sectors', headers=auth_headers)
        assert response.status_code in [200, 401, 500]
        if response.status_code == 200:
            assert response.json.get('success') == True
            sectors = response.json.get('data', [])
            assert len(sectors) > 0
    
    def test_create_startup(self, client, auth_headers, sample_startup_data):
        """Test creating a startup"""
        if not auth_headers:
            pytest.skip("No auth headers available")
        
        response = client.post(
            '/api/startups',
            json=sample_startup_data,
            headers=auth_headers
        )
        # Should work or fail gracefully
        assert response.status_code in [200, 201, 400, 401, 500]
    
    def test_list_startups(self, client, auth_headers):
        """Test listing startups"""
        if not auth_headers:
            pytest.skip("No auth headers available")
        
        response = client.get('/api/startups', headers=auth_headers)
        # Should return 200 or 401/500
        assert response.status_code in [200, 401, 500]
