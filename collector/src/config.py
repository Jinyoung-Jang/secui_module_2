"""
Configuration loader for the metrics collector.
"""

import os
import re
import yaml
from typing import Any, Dict
from pathlib import Path


class Config:
    """Configuration manager for the collector."""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to the configuration file.
                        If None, looks for config/collector-config.yaml
        """
        if config_path is None:
            # Default config path relative to this file
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "collector-config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load and parse the YAML configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_text = f.read()

        # Replace environment variables
        config_text = self._replace_env_vars(config_text)

        config = yaml.safe_load(config_text)
        return config

    def _replace_env_vars(self, text: str) -> str:
        """
        Replace ${VAR_NAME} patterns with environment variable values.

        Args:
            text: Text containing environment variable patterns

        Returns:
            Text with environment variables replaced
        """
        pattern = r'\$\{([^}]+)\}'

        def replace(match):
            var_name = match.group(1)
            value = os.getenv(var_name)
            if value is None:
                # Keep the original pattern if env var not found
                return match.group(0)
            return value

        return re.sub(pattern, replace, text)

    def _validate_config(self):
        """Validate required configuration fields."""
        required_fields = [
            ('collector', 'interval'),
            ('collector', 'server_url'),
        ]

        for *path, field in required_fields:
            config_section = self.config
            for key in path:
                if key not in config_section:
                    raise ValueError(f"Missing required configuration: {'.'.join(path)}.{field}")
                config_section = config_section[key]

            if field not in config_section:
                raise ValueError(f"Missing required configuration: {'.'.join(path)}.{field}")

    def get(self, *keys, default=None):
        """
        Get a configuration value using dot notation.

        Args:
            *keys: Keys to traverse (e.g., 'collector', 'interval')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        value = self.config
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return default
            value = value[key]
        return value

    @property
    def collector_interval(self) -> int:
        """Get collector interval in seconds."""
        return self.get('collector', 'interval', default=5)

    @property
    def server_url(self) -> str:
        """Get API server URL."""
        return self.get('collector', 'server_url')

    @property
    def api_key(self) -> str:
        """Get API key."""
        return self.get('collector', 'api_key', default='')

    @property
    def hostname(self) -> str:
        """Get hostname or auto-detect."""
        hostname = self.get('collector', 'hostname', default='')
        if not hostname:
            import socket
            hostname = socket.gethostname()
        return hostname

    @property
    def buffer_dir(self) -> Path:
        """Get buffer directory path."""
        buffer_dir = self.get('collector', 'buffer_dir', default='./buffer')
        return Path(buffer_dir)

    @property
    def buffer_max_size(self) -> int:
        """Get buffer max size in MB."""
        return self.get('collector', 'buffer_max_size', default=100)

    def is_metric_enabled(self, metric_type: str) -> bool:
        """
        Check if a metric type is enabled.

        Args:
            metric_type: Type of metric (cpu, memory, disk, network)

        Returns:
            True if enabled, False otherwise
        """
        return self.get('metrics', metric_type, 'enabled', default=False)

    def get_metric_interval(self, metric_type: str) -> int:
        """
        Get metric collection interval.

        Args:
            metric_type: Type of metric (cpu, memory, disk, network)

        Returns:
            Interval in seconds
        """
        interval = self.get('metrics', metric_type, 'interval', default=0)
        if interval == 0:
            interval = self.collector_interval
        return interval

    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.get('logging', 'level', default='INFO')

    @property
    def log_file(self) -> str:
        """Get log file path."""
        return self.get('logging', 'file', default='')
