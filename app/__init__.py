
import logging
from flask import Flask
from config import DevAssistantConfig
from app.services import EnhancedServiceChecker

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-assistant-secret-key'

checker = EnhancedServiceChecker()
config = DevAssistantConfig()

from . import routes
