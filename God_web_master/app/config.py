"""
Advanced Configuration Management
Supports YAML config, environment variables, and runtime overrides.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class SecurityConfig:
    """Security-related configuration."""
    encrypt_output: bool = True
    encryption_key: Optional[str] = None
    use_random_user_agent: bool = True
    rate_limit_requests: int = 10  # requests per second
    verify_ssl: bool = True
    timeout: int = 10

@dataclass
class OutputConfig:
    """Output-related configuration."""
    output_dir: str = "output"
    log_dir: str = "logs"
    default_format: str = "json"  # json, html, csv
    save_history: bool = True
    compress_old_reports: bool = True

@dataclass
class UIConfig:
    """UI/UX configuration."""
    enable_colors: bool = True
    show_progress_bar: bool = True
    interactive_help: bool = True
    language: str = "en"

@dataclass
class AppConfig:
    """Main application configuration."""
    security: SecurityConfig = field(default_factory=SecurityConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def load(cls, config_path: str = "config/settings.yaml") -> 'AppConfig':
        """Load configuration from YAML file with environment variable overrides."""
        config = cls()
        
        # Load YAML if exists
        if Path(config_path).exists():
            with open(config_path, 'r') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    config._update_from_dict(yaml_config)
        
        # Override with environment variables
        config._override_from_env()
        
        # Ensure output directories exist
        os.makedirs(config.output.output_dir, exist_ok=True)
        os.makedirs(config.output.log_dir, exist_ok=True)
        
        return config
    
    def _update_from_dict(self, data: dict):
        """Update configuration from dictionary."""
        if 'security' in data:
            for key, value in data['security'].items():
                if hasattr(self.security, key):
                    setattr(self.security, key, value)
        if 'output' in data:
            for key, value in data['output'].items():
                if hasattr(self.output, key):
                    setattr(self.output, key, value)
        if 'ui' in data:
            for key, value in data['ui'].items():
                if hasattr(self.ui, key):
                    setattr(self.ui, key, value)
    
    def _override_from_env(self):
        """Override configuration from environment variables."""
        env_mappings = {
            'GWM_ENCRYPT_OUTPUT': ('security', 'encrypt_output', bool),
            'GWM_ENCRYPTION_KEY': ('security', 'encryption_key', str),
            'GWM_OUTPUT_DIR': ('output', 'output_dir', str),
            'GWM_VERIFY_SSL': ('security', 'verify_ssl', bool),
            'GWM_TIMEOUT': ('security', 'timeout', int),
        }
        
        for env_var, (section, attr, type_func) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                section_obj = getattr(self, section)
                setattr(section_obj, attr, type_func(value))