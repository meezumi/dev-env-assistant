import logging
from flask import Flask

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-assistant-secret-key"

from app.services import EnhancedServiceChecker
from config import DevAssistantConfig

checker = EnhancedServiceChecker()
config = DevAssistantConfig()

from app import routes
