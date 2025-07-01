import pytest
from unittest.mock import MagicMock, patch
import requests
from src.utils.decorators import retry_on_failure

def test_retry_success_on_first_try():
    """Tests that the decorator doesn't interfere with a successful function call."""
    mock_func = MagicMock(return_value="Success")
    
    decorated_func = retry_on_failure(max_retries=3)(mock_func)
    result = decorated_func()
    
    assert result == "Success"
    mock_func.assert_called_once()
