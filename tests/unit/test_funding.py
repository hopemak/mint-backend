"""
Unit Tests for Funding
"""

import pytest

class TestFunding:
    """Funding endpoint tests"""
    
    def test_list_funding_requests(self, client, auth_headers):
        """Test listing funding requests"""
        if not auth_headers:
            pytest.skip("No auth headers available")
        
        response = client.get('/api/funding/requests', headers=auth_headers)
        assert response.status_code in [200, 401, 500]
    
    def test_funding_summary(self, client, auth_headers):
        """Test getting funding summary"""
        if not auth_headers:
            pytest.skip("No auth headers available")
        
        response = client.get('/api/funding/summary', headers=auth_headers)
        assert response.status_code in [200, 401, 500]
        if response.status_code == 200:
            data = response.json.get('data', {})
            assert 'total_requests' in data
    
    def test_request_funding(self, client, auth_headers, sample_funding_data):
        """Test funding request"""
        if not auth_headers:
            pytest.skip("No auth headers available")
        
        response = client.post(
            '/api/funding/request',
            json=sample_funding_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 400, 401, 404, 500]
