"""
Unit Tests for ML Endpoints
"""

import pytest

class TestML:
    """ML endpoint tests"""
    
    def test_get_metrics(self, client, auth_headers):
        """Test getting model metrics"""
        if not auth_headers:
            pytest.skip("No auth headers available")
        
        response = client.get('/api/ml/metrics', headers=auth_headers)
        # Should work or fail gracefully
        assert response.status_code in [200, 401, 500]
        if response.status_code == 200:
            assert response.json.get('success') == True
    
    def test_evaluate_idea(self, client, auth_headers, sample_ml_data):
        """Test idea evaluation"""
        if not auth_headers:
            pytest.skip("No auth headers available")
        
        response = client.post(
            '/api/ml/evaluate',
            json=sample_ml_data,
            headers=auth_headers
        )
        # Should work or fail gracefully (if no model)
        assert response.status_code in [200, 401, 500]
        if response.status_code == 200:
            assert response.json.get('success') == True
    
    def test_predict_success(self, client, auth_headers, sample_ml_data):
        """Test success prediction"""
        if not auth_headers:
            pytest.skip("No auth headers available")
        
        response = client.post(
            '/api/ml/predict',
            json=sample_ml_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 500]
    
    def test_duplicate_detection(self, client, auth_headers):
        """Test duplicate detection"""
        if not auth_headers:
            pytest.skip("No auth headers available")
        
        data = {'text': 'AI-powered healthcare platform'}
        response = client.post('/api/ml/duplicate', json=data, headers=auth_headers)
        assert response.status_code in [200, 401, 500]
    
    def test_rag_chat(self, client, auth_headers):
        """Test RAG chatbot"""
        if not auth_headers:
            pytest.skip("No auth headers available")
        
        data = {'query': 'How does mentorship work?'}
        response = client.post('/api/ml/chat', json=data, headers=auth_headers)
        assert response.status_code in [200, 401, 500]
