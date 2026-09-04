"""
pymconfig.py - Metupy Project Configuration.

Edit values below to configure your site.
All variables MUST be UPPERCASE.
"""

from pathlib import Path

SITE_NAME = "docs"
SITE_VERSION = "1.0.0"
SITE_DESCRIPTION = "Built with Metupy SSG"
SITE_AUTHOR = "Your Name"
SITE_KEYWORDS = ["metupy", "static-site", "ssg"]
SITE_LANG = "en"
SITE_TIMEZONE = "UTC"

SITE_URL = "http://localhost:3155"
SITE_BASE_URL = "/"
SITE_CANONICAL_URL = f"{SITE_URL}/"

BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "docs"
OUTPUT_DIR = Path.home() / ".metupy" / "output" / "docs"
THEME_DIR = Path.home() / ".metupy" / "themes" / "peradocs"
ASSETS_DIR = CONTENT_DIR / "assets"
DATA_DIR = BASE_DIR / "data"

ACTIVE_THEME = "peradocs"
ACTIVE_PLUGINS = []

BUILD_MINIFY_HTML = False
BUILD_MINIFY_CSS = False
BUILD_MINIFY_JS = False
BUILD_GENERATE_SITEMAP = True
BUILD_GENERATE_FEED = True
BUILD_CACHE_ENABLED = True
BUILD_PRETTY_URLS = True

DEV_HOST = "localhost"
DEV_PORT = 3155
DEV_DEBUG = True
DEV_LIVE_RELOAD = True
DEV_OPEN_BROWSER = True

STUDIO_ENABLED = True
STUDIO_HOST = "localhost"
STUDIO_PORT = 3154
STUDIO_AUTO_OPEN = True
STUDIO_REQUIRE_LOGIN = True

DB_ENGINE = "sqlite"
DB_PATH = DATA_DIR / "metupy.db"

CACHE_ENABLED = False
CACHE_TYPE = "memory"

SECRET_KEY = "dev-secret-key-change-in-production"

MARKDOWN_EXTENSIONS = ["extra", "tables", "fenced_code"]
MARKDOWN_EXTENSION_CONFIGS = {}

JINJA_EXTENSIONS = ["jinja2.ext.do", "jinja2.ext.loopcontrols"]

DEBUG = True
TESTING = False
PRODUCTION = False
