
import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

CONFIG_FILE = 'dev_assistant_config.json'

class DevAssistantConfig:
    """Configuration management for the assistant"""

    def __init__(self):
        self.config_file = CONFIG_FILE
        self.default_config = {
            "services": {
                "web_dev": [
                    {"name": "React Dev Server", "type": "http", "url": "http://localhost:3000"},
                    {"name": "Vue Dev Server", "type": "http", "url": "http://localhost:8080"},
                    {"name": "Angular Dev Server", "type": "http", "url": "http://localhost:4200"},
                    {"name": "Next.js Dev Server", "type": "http", "url": "http://localhost:3000"},
                ],
                "backend": [
                    {"name": "Express Server", "type": "http", "url": "http://localhost:3000"},
                    {"name": "Django Dev Server", "type": "http", "url": "http://localhost:8000"},
                    {"name": "Flask Dev Server", "type": "http", "url": "http://localhost:5000"},
                    {"name": "FastAPI Server", "type": "http", "url": "http://localhost:8000"},
                    {"name": "Rails Server", "type": "http", "url": "http://localhost:3000"},
                ],
                "databases": [
                    {"name": "PostgreSQL", "type": "port", "port": 5432},
                    {"name": "MySQL", "type": "port", "port": 3306},
                    {"name": "MongoDB", "type": "port", "port": 27017},
                    {"name": "Redis", "type": "port", "port": 6379},
                ],
                "tools": [
                    {"name": "Docker Engine API", "type": "http", "url": "http://localhost:2375"},
                    {"name": "Elasticsearch", "type": "http", "url": "http://localhost:9200"},
                    {"name": "RabbitMQ Management", "type": "http", "url": "http://localhost:15672"},
                    {"name": "Mailhog", "type": "http", "url": "http://localhost:8025"},
                ]
            },
            "monitoring": {
                "enabled": True,
                "check_interval": 60,  # seconds
                "alert_thresholds": {
                    "response_time_warning": 2000,  # ms
                    "downtime_warning_threshold": 5  # minutes
                }
            },
            "notifications": {
                "email_enabled": False,
                "slack_enabled": False,
                "webhook_enabled": False
            }
        }
        self.load_config()

    def load_config(self):
        """Load configuration from file or create default if not exists"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                    # Merge with defaults for any missing keys
                    self._merge_defaults()
            else:
                self.config = self.default_config.copy()
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = self.default_config.copy()

    def _merge_defaults(self):
        """Merge loaded config with defaults"""
        def merge_dict(target, source):
            for key, value in source.items():
                if key not in target:
                    target[key] = value
                elif isinstance(value, dict) and isinstance(target[key], dict):
                    merge_dict(target[key], value)

        merge_dict(self.config, self.default_config)

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get_services(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get services configuration"""
        if category:
            return self.config.get("services", {}).get(category, [])
        return self.config.get("services", {})
