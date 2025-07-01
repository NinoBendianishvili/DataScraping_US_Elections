import pytest
import yaml
from unittest.mock import patch, mock_open
from src.utils.config_loader import load_config

# A sample YAML content string
SAMPLE_YAML_CONTENT = """
scraper:
  timeout: 15
  user_agent: 'MyTestScraper/1.0'
"""

@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open, read_data=SAMPLE_YAML_CONTENT)
def test_load_config_success(mock_file, mock_exists):
    """Tests successful loading and parsing of a YAML file."""
    config = load_config("dummy/path.yaml")
    
    mock_exists.assert_called_once_with("dummy/path.yaml")
    mock_file.assert_called_once_with("dummy/path.yaml", 'r', encoding='utf-8')
    
    assert config is not None
    assert config['scraper']['timeout'] == 15
    assert config['scraper']['user_agent'] == 'MyTestScraper/1.0'

@patch('os.path.exists', return_value=False)
def test_load_config_file_not_found(mock_exists, caplog):
    """Tests the case where the config file does not exist."""
    config = load_config("nonexistent/path.yaml")
    
    mock_exists.assert_called_once_with("nonexistent/path.yaml")
    assert config is None
    assert "Configuration file not found" in caplog.text

@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open, read_data="key: - invalid yaml")
def test_load_config_yaml_error(mock_file, mock_exists, caplog):
    """Tests handling of a malformed YAML file."""
    config = load_config("bad/format.yaml")
    
    assert config is None
    assert "Error parsing the YAML configuration file" in caplog.text