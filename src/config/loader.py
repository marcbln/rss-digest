"""
Config loader for TOML-based digest configurations.
Supports multiple digest configs in the configs/ directory.
"""

import os
import toml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def load_config(config_name: str, configs_dir: str = "configs") -> Dict[str, Any]:
    """
    Load a TOML config file from the configs directory.
    
    Args:
        config_name: Name of the config file (with or without .toml extension)
        configs_dir: Directory containing config files (default: configs)
    
    Returns:
        Dictionary containing the parsed config
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is missing required fields
    """
    # Ensure .toml extension
    if not config_name.endswith('.toml'):
        config_name += '.toml'
    
    config_path = Path(configs_dir) / config_name
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            f"Available configs: {list_available_configs(configs_dir)}"
        )
    
    logger.info(f"Loading config from: {config_path}")
    config = toml.load(config_path)
    
    # Validate required fields
    required_fields = ['name', 'feeds']
    missing = [f for f in required_fields if f not in config]
    if missing:
        raise ValueError(f"Config missing required fields: {missing}")
    
    # Set defaults for optional fields
    config.setdefault('description', '')
    config.setdefault('schedule', 'weekly')
    config.setdefault('days_lookback', 7)
    config.setdefault('email_subject', f"{config['name']} Digest")
    config.setdefault('sender_name', config['name'])
    
    # Validate feeds
    if not isinstance(config['feeds'], dict) or not config['feeds']:
        raise ValueError("Config 'feeds' must be a non-empty dictionary")
    
    logger.info(f"Loaded config: {config['name']} ({len(config['feeds'])} feeds)")
    return config


def list_available_configs(configs_dir: str = "configs") -> list:
    """
    List all available config files in the configs directory.
    
    Args:
        configs_dir: Directory containing config files
    
    Returns:
        List of config file names (without .toml extension)
    """
    configs_path = Path(configs_dir)
    if not configs_path.exists():
        return []
    
    return [
        f.stem for f in configs_path.glob("*.toml")
        if f.is_file()
    ]


def get_config_info(config_name: str, configs_dir: str = "configs") -> Dict[str, Any]:
    """
    Get summary info about a config without loading full prompt.
    
    Args:
        config_name: Name of the config file
        configs_dir: Directory containing config files
    
    Returns:
        Dictionary with config metadata
    """
    config = load_config(config_name, configs_dir)
    return {
        'name': config['name'],
        'description': config.get('description', ''),
        'schedule': config.get('schedule', 'weekly'),
        'feed_count': len(config['feeds']),
        'feeds': list(config['feeds'].keys())
    }
