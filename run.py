import os
import json
from app import app

CONFIG_FILE = "dev_assistant_config.json"


def ensure_directories():
    """Ensure necessary directories exist"""
    directories = ["app/templates", "app/static/css", "app/static/js"]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def create_config_file():
    """Create default config file if it doesn't exist"""
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "services": {
                "web_dev": [
                    {
                        "name": "React Dev Server",
                        "type": "http",
                        "url": "http://localhost:3000",
                    },
                    {
                        "name": "Vue Dev Server",
                        "type": "http",
                        "url": "http://localhost:8080",
                    },
                    {
                        "name": "Angular Dev Server",
                        "type": "http",
                        "url": "http://localhost:4200",
                    },
                    {
                        "name": "Next.js Dev Server",
                        "type": "http",
                        "url": "http://localhost:3000",
                    },
                ],
                "backend": [
                    {
                        "name": "Express Server",
                        "type": "http",
                        "url": "http://localhost:3000",
                    },
                    {
                        "name": "Django Dev Server",
                        "type": "http",
                        "url": "http://localhost:8000",
                    },
                    {
                        "name": "Flask Dev Server",
                        "type": "http",
                        "url": "http://localhost:5000",
                    },
                    {
                        "name": "FastAPI Server",
                        "type": "http",
                        "url": "http://localhost:8000",
                    },
                    {
                        "name": "Rails Server",
                        "type": "http",
                        "url": "http://localhost:3000",
                    },
                ],
                "databases": [
                    {"name": "PostgreSQL", "type": "port", "port": 5432},
                    {"name": "MySQL", "type": "port", "port": 3306},
                    {"name": "MongoDB", "type": "port", "port": 27017},
                    {"name": "Redis", "type": "port", "port": 6379},
                ],
                "tools": [
                    {
                        "name": "Docker Engine API",
                        "type": "http",
                        "url": "http://localhost:2375",
                    },
                    {
                        "name": "Elasticsearch",
                        "type": "http",
                        "url": "http://localhost:9200",
                    },
                    {
                        "name": "RabbitMQ Management",
                        "type": "http",
                        "url": "http://localhost:15672",
                    },
                    {"name": "Mailhog", "type": "http", "url": "http://localhost:8025"},
                ],
            },
            "monitoring": {
                "enabled": True,
                "check_interval": 60,
                "alert_thresholds": {
                    "response_time_warning": 2000,
                    "downtime_warning_threshold": 5,
                },
            },
            "notifications": {
                "email_enabled": False,
                "slack_enabled": False,
                "webhook_enabled": False,
            },
        }

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)

        print(f"Created default configuration file: {CONFIG_FILE}")


def main():
    """Main application entry point"""
    print("Starting Dev Env Fetcher...")

    # Setup
    ensure_directories()
    create_config_file()

    print("Setup complete!")
    print("Starting web server on http://localhost:5000")
    print("Access the dashboard at: http://localhost:5000")

    # Start the Flask application
    app.run(debug=True, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
