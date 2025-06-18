"""
Utility for loading the central YAML configuration file for the project.
"""
import yaml
import os
import logging

# Set up a logger for this module
logger = logging.getLogger(__name__)

# The default path is relative to the project root directory (where main.py is run)
DEFAULT_CONFIG_PATH = "config/settings.yaml"

def load_config(path: str = DEFAULT_CONFIG_PATH) -> dict | None:
    """
    Loads the YAML configuration file from the given path.

    Args:
        path (str): The path to the configuration file.

    Returns:
        A dictionary containing the configuration settings, or None if
        the file cannot be found or parsed.
    """
    # Check if the configuration file exists before trying to open it.
    if not os.path.exists(path):
        # Log a specific, helpful error message.
        logger.error(f"Configuration file not found at the expected path: {os.path.abspath(path)}")
        logger.error("Please ensure that 'config/settings.yaml' exists in your project's root directory.")
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Successfully loaded configuration from '{path}'")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Error parsing the YAML configuration file at '{path}': {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading the config file '{path}': {e}", exc_info=True)
        return None