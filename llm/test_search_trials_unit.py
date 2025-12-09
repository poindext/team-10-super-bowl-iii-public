"""
Unit tests for search_trials_tool using pytest and mocking.
Run with: pytest test_search_trials_unit.py -v
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from search_trials_tool import search_trials_tool, _get_auth


class TestGetAuth:
    """Test the _get_auth function with different configurations."""

    def test_basic_auth(self):
        """Test Basic Authentication."""
        with patch.dict(os.environ, {
            'IRIS_USERNAME': 'testuser',
            'IRIS_PASSWORD': 'testpass'
        }):
            auth = _get_auth()
            assert auth is not None
            assert hasattr(auth, 'username')
            assert auth.username == 'testuser'
            assert auth.password == 'testpass'

    def test_bearer_token(self):
        """Test Bearer Token authentication."""
        with patch.dict(os.environ, {
            'IRIS_BEARER_TOKEN': 'test_token_123'
        }, clear=True):
            auth = _get_auth()
            assert auth is not None
            assert isinstance(auth, dict)
            assert 'Authorization' in auth
            assert auth['Authorization'] == 'Bearer test_token_123'

    def test_api_key(self):
        """Test API Key authentication."""
        with patch.dict(os.environ, {
            'IRIS_API_KEY': 'test_api_key_456'
        }, clear=True):
            auth = _get_auth()
            assert auth is not None
            assert isinstance(auth, dict)
            assert 'X-API-Key' in auth
            assert auth['X-API-Key'] == 'test_api_key_456'

    def test_no_auth(self):
        """Test when no authentication is configured."""
        with patch.dict(os.environ, {}, clear=True):
            auth = _get_auth()
            assert auth is None

    def test_priority_basic_over_bearer(self):
        """Test that Basic Auth takes priority over Bearer Token."""
        with patch.dict(os.environ, {
            'IRIS_USERNAME': 'testuser',
            'IRIS_PASSWORD': 'testpass',
            'IRIS_BEARER_TOKEN': 'test_token'
        }):
            auth = _get_auth()
            assert auth is not None
            assert hasattr(auth, 'username')  # Should be Basic Auth, not Bearer


class TestSearchTrialsTool:
    """Test the search_trials_tool function."""

    @patch('search_trials_tool.requests.post')
    def test_successful_request_with_basic_auth(self, mock_post):
        """Test successful API call with Basic Auth."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'trials': [
                {'NCTID': 'NCT123', 'SearchText': 'Test trial'}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Set up Basic Auth
        with patch.dict(os.environ, {
            'IRIS_USERNAME': 'testuser',
            'IRIS_PASSWORD': 'testpass'
        }):
            result = search_trials_tool("diabetes", maxRows=10)

        # Verify the call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json']['queryText'] == "diabetes"
        assert call_args[1]['json']['maxRows'] == 10
        assert call_args[1]['auth'] is not None
        assert result['trials'][0]['NCTID'] == 'NCT123'

    @patch('search_trials_tool.requests.post')
    def test_successful_request_with_bearer_token(self, mock_post):
        """Test successful API call with Bearer Token."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'trials': []}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Set up Bearer Token
        with patch.dict(os.environ, {
            'IRIS_BEARER_TOKEN': 'test_token'
        }, clear=True):
            result = search_trials_tool("cancer treatment")

        # Verify the call
        call_args = mock_post.call_args
        assert call_args[1]['headers']['Authorization'] == 'Bearer test_token'
        assert call_args[1]['auth'] is None

    @patch('search_trials_tool.requests.post')
    def test_successful_request_with_api_key(self, mock_post):
        """Test successful API call with API Key."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'trials': []}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Set up API Key
        with patch.dict(os.environ, {
            'IRIS_API_KEY': 'test_key'
        }, clear=True):
            result = search_trials_tool("heart disease")

        # Verify the call
        call_args = mock_post.call_args
        assert call_args[1]['headers']['X-API-Key'] == 'test_key'
        assert call_args[1]['auth'] is None

    @patch('search_trials_tool.requests.post')
    def test_request_without_maxrows(self, mock_post):
        """Test that maxRows is optional."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'trials': []}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {}, clear=True):
            search_trials_tool("test query")

        # Verify maxRows is not in payload
        call_args = mock_post.call_args
        assert 'maxRows' not in call_args[1]['json']

    @patch('search_trials_tool.requests.post')
    def test_http_error_handling(self, mock_post):
        """Test that HTTP errors are raised."""
        # Mock HTTP error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):
                search_trials_tool("test query")

    @patch('search_trials_tool.requests.post')
    def test_correct_url(self, mock_post):
        """Test that the correct URL is called."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'trials': []}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {}, clear=True):
            search_trials_tool("test")

        # Verify URL
        call_args = mock_post.call_args
        url = call_args[0][0]
        assert 'ec2-98-82-129-136.compute-1.amazonaws.com' in url
        assert '/i4h/ctgov/VectorTrialSearch' in url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

