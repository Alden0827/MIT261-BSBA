import os
from dotenv import load_dotenv

# Load environment variables from .env in the project root
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# APPLICATION SETTINTS ----------------------------------------------------------
DEFAULT_PAGE_TITLE = "MIT261-BSBA"
# APP_TITLE = "🏫 University DASHBOARD"
APP_TITLE = "🏫 BSBA Department Academic Records Management System"
DB_NAME = "mit261"

# DATABASE CONFIGURATION --------------------------------------------------------
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGODB_CLUSTER_INSTANCE = os.getenv("MONGODB_CLUSTER_INSTANCE")
# MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")

MONGODB_URI = (
    f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}"
    f"@cluster0.{MONGODB_CLUSTER_INSTANCE}.mongodb.net/{DB_NAME}"
)

# CACHING SETTINGS -------------------------------------------------------------
# CACHE_MAX_AGE = 3600
CACHE_MAX_AGE = 0 #disable caching

