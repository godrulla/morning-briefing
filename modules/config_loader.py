"""
Configuration Loader Module
Handles loading and validating configuration from YAML files and keychain
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger('morning-briefing.config')


class ConfigLoader:
    """Loads and manages configuration from YAML files"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration loader

        Args:
            config_dir: Directory containing config files. Defaults to script directory.
        """
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent
        else:
            self.config_dir = Path(config_dir)

        self.config_file = self.config_dir / 'config.yaml'
        self.secrets_file = self.config_dir / 'secrets.yaml'

        self.config: Dict[str, Any] = {}
        self.secrets: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from YAML files

        Returns:
            Combined configuration dictionary
        """
        # Load main config
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_file}\n"
                f"Please copy config.example.yaml to config.yaml and customize it."
            )

        with open(self.config_file, 'r') as f:
            self.config = yaml.safe_load(f)
            logger.info("Loaded configuration from config.yaml")

        # Load secrets
        if not self.secrets_file.exists():
            raise FileNotFoundError(
                f"Secrets file not found: {self.secrets_file}\n"
                f"Please copy secrets.example.yaml to secrets.yaml and add your credentials."
            )

        with open(self.secrets_file, 'r') as f:
            self.secrets = yaml.safe_load(f)
            logger.info("Loaded secrets from secrets.yaml")

        # Check if using keychain
        if self.secrets.get('use_keychain', False):
            self._load_from_keychain()

        # Validate configuration
        self._validate_config()

        return self.get_all()

    def _load_from_keychain(self):
        """Load secrets from macOS keychain if enabled"""
        try:
            import keyring

            # Try to get GitHub token from keychain
            github_token = keyring.get_password('morning-briefing', 'github_token')
            if github_token:
                self.secrets['github']['access_token'] = github_token
                logger.info("Loaded GitHub token from keychain")
        except ImportError:
            logger.warning("keyring module not available, using secrets from file")
        except Exception as e:
            logger.warning(f"Failed to load from keychain: {e}")

    def _validate_config(self):
        """Validate required configuration fields"""
        required_fields = {
            'config': ['user', 'email', 'github', 'calendar'],
            'secrets': ['google', 'github']
        }

        # Validate main config
        for field in required_fields['config']:
            if field not in self.config:
                raise ValueError(f"Missing required configuration field: {field}")

        # Validate secrets
        for field in required_fields['secrets']:
            if field not in self.secrets:
                raise ValueError(f"Missing required secrets field: {field}")

        # Validate Google credentials path
        google_creds = self.secrets['google'].get('credentials_file')
        if google_creds and not Path(google_creds).exists():
            logger.warning(
                f"Google credentials file not found: {google_creds}\n"
                f"You'll need to download credentials.json from Google Cloud Console"
            )

        # Validate GitHub token
        github_token = self.secrets['github'].get('access_token')
        if not github_token or github_token == 'ghp_your_github_token_here':
            logger.warning(
                "GitHub access token not configured. "
                "Please add your token to secrets.yaml"
            )

        logger.info("Configuration validation passed")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key (supports dot notation)

        Args:
            key: Configuration key (e.g., 'user.email')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_secret(self, key: str, default: Any = None) -> Any:
        """
        Get a secret value by key (supports dot notation)

        Args:
            key: Secret key (e.g., 'github.access_token')
            default: Default value if key not found

        Returns:
            Secret value or default
        """
        keys = key.split('.')
        value = self.secrets

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration and secrets combined

        Returns:
            Combined configuration dictionary
        """
        return {
            'config': self.config,
            'secrets': self.secrets
        }

    def get_google_credentials_path(self) -> str:
        """Get path to Google OAuth credentials file"""
        return self.get_secret('google.credentials_file')

    def get_google_token_path(self) -> str:
        """Get path to Google OAuth token file"""
        return self.get_secret('google.token_file')

    def get_github_token(self) -> str:
        """Get GitHub access token"""
        return self.get_secret('github.access_token')

    def get_user_email(self) -> str:
        """Get user's email address"""
        return self.get('user.email')

    def get_send_to_email(self) -> str:
        """Get email address to send briefings to"""
        return self.get('email.send_to', self.get_user_email())


def load_config(config_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to load configuration

    Args:
        config_dir: Directory containing config files

    Returns:
        Combined configuration dictionary
    """
    loader = ConfigLoader(config_dir)
    return loader.load()
