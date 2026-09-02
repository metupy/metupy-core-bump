"""pymconfig.py — Metupy Project Configuration File.

Edit values below to configure your site.
All variables MUST be UPPERCASE.
"""

import os
from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env file if exists
load_dotenv()

# ═══════════════════════════════════════════════════════
# Site Information
# ═══════════════════════════════════════════════════════
SITE_NAME = os.getenv('METUPY_SITE_NAME', 'My Metupy Site')
SITE_VERSION = "1.0.0"
SITE_DESCRIPTION = "Built with Metupy SSG — Fast, modern static site generator"
SITE_AUTHOR = "Your Name"
SITE_KEYWORDS = ["metupy", "static-site", "documentation", "ssg"]
SITE_LANG = "id"
SITE_TIMEZONE = "Asia/Jakarta"

# ═══════════════════════════════════════════════════════
# Site URL & Deployment
# ═══════════════════════════════════════════════════════
SITE_URL = os.getenv('METUPY_SITE_URL', 'http://localhost:3000')
SITE_BASE_URL = "/"
SITE_CANONICAL_URL = f"{SITE_URL}/"

# ═══════════════════════════════════════════════════════
# GitHub Repository & Deployment
# ═══════════════════════════════════════════════════════
GH_USER = f"{SITE_AUTHOR}"
GH_REPO = f"{SITE_NAME}"
GH_BRANCH = "main"
GH_REPO_URL = f"https://github.com/{GH_USER}/{GH_REPO}.git"
GH_PAGES_BRANCH = "gh-pages"

# ═══════════════════════════════════════════════════════
# Build Paths
# ═══════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content"
OUTPUT_DIR = BASE_DIR / "public"
THEME_DIR = BASE_DIR / "themes" / "peradocs"
ASSETS_DIR = CONTENT_DIR / "assets"
TEMPLATES_DIR = BASE_DIR / "templates"
PLUGINS_DIR = BASE_DIR / "plugins"
WIDGETS_DIR = BASE_DIR / "widgets"
DATA_DIR = BASE_DIR / "data"

# ═══════════════════════════════════════════════════════
# Theme Configuration
# ═══════════════════════════════════════════════════════
ACTIVE_THEME = "peradocs"
THEME_SETTINGS = {
    "dark_mode": True,
    "custom_css": True,
    "custom_js": True,
    "color_scheme": "default",
    "font_family": "Inter",
    "code_theme": "github-dark",
}

# ═══════════════════════════════════════════════════════
# Plugin Configuration
# ═══════════════════════════════════════════════════════
ACTIVE_PLUGINS = [
    "metupy-plugin-seo",
    "metupy-plugin-comments",
    "metupy-plugin-search",
    "metupy-plugin-sitemap",
    "metupy-plugin-rss",
]

PLUGIN_SETTINGS = {
    "comments": {
        "enabled": True,
        "moderation": True,
        "allow_anonymous": False,
        "nested_replies": True,
        "max_depth": 3,
        "rate_limit": {
            "per_minute": 5,
            "per_hour": 20,
        },
    },
    "search": {
        "enabled": True,
        "index_content": True,
        "index_metadata": True,
        "min_chars": 2,
    },
    "seo": {
        "generate_meta": True,
        "generate_og": True,
        "generate_twitter": True,
        "auto_description": True,
    },
}

# ═══════════════════════════════════════════════════════
# Build Settings
# ═══════════════════════════════════════════════════════
BUILD_MINIFY_HTML = False
BUILD_MINIFY_CSS = False
BUILD_MINIFY_JS = False
BUILD_GENERATE_SITEMAP = True
BUILD_GENERATE_FEED = True
BUILD_CACHE_ENABLED = True
BUILD_PRETTY_URLS = True
BUILD_INCREMENTAL = True
BUILD_PARALLEL = True

# ═══════════════════════════════════════════════════════
# Server Configuration
# ═══════════════════════════════════════════════════════
DEV_HOST = "localhost"
DEV_PORT = 3000
DEV_DEBUG = True
DEV_LIVE_RELOAD = True
DEV_WATCH_FILES = True
DEV_OPEN_BROWSER = True
DEV_POLL_INTERVAL = 1  # seconds

# ═══════════════════════════════════════════════════════
# Studio Configuration
# ═══════════════════════════════════════════════════════
STUDIO_ENABLED = True
STUDIO_HOST = "localhost"
STUDIO_PORT = 3001
STUDIO_AUTO_OPEN = True
STUDIO_REQUIRE_LOGIN = True
STUDIO_SETUP_REQUIRED = True

# ═══════════════════════════════════════════════════════
# Database Configuration
# ═══════════════════════════════════════════════════════
DB_ENGINE = "sqlite"  # sqlite, postgresql, mysql
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "metupy_db")
DB_PATH = DATA_DIR / "metupy.db"

# ═══════════════════════════════════════════════════════
# Cache Configuration (REDIS)
# ═══════════════════════════════════════════════════════
CACHE_ENABLED = True
CACHE_TYPE = "redis"  # redis, memory, file
CACHE_HOST = os.environ.get("REDIS_HOST", "localhost")
CACHE_PORT = int(os.environ.get("REDIS_PORT", 6379))
CACHE_DB = int(os.environ.get("REDIS_DB", 0))
CACHE_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
CACHE_TTL = 3600  # seconds
CACHE_PREFIX = "metupy"

# ═══════════════════════════════════════════════════════
# Security Configuration
# ═══════════════════════════════════════════════════════
SECRET_KEY = os.getenv('METUPY_SECRET_KEY', 'dev-secret-key')
TOKEN_EXPIRY = 3600  # 1 hour
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
CSRF_ENABLED = True
CORS_ENABLED = True
CORS_ORIGINS = ["*"]

# ═══════════════════════════════════════════════════════
# Markdown Configuration
# ═══════════════════════════════════════════════════════
MARKDOWN_EXTENSIONS = [
    "extra",
    "codehilite",
    "toc",
    "tables",
    "fenced_code",
    "footnotes",
    "admonition",
    "meta",
]

MARKDOWN_EXTENSION_CONFIGS = {
    "codehilite": {
        "css_class": "highlight",
        "guess_lang": True,
        "linenums": True,
    },
    "toc": {
        "permalink": True,
        "permalink_class": "header-link",
        "toc_depth": "2-4",
    },
}

# ═══════════════════════════════════════════════════════
# Jinja2 Configuration
# ═══════════════════════════════════════════════════════
JINJA_EXTENSIONS = [
    "jinja2.ext.do",
    "jinja2.ext.loopcontrols",
    "jinja2.ext.i18n",
]

JINJA_FILTERS = {
    "markdown": "metupy.utils.filters.markdown_filter",
    "format_date": "metupy.utils.filters.format_date_filter",
    "slugify": "metupy.utils.filters.slugify_filter",
}

JINJA_GLOBALS = {
    "site": "metupy.utils.globals.get_site_info",
    "theme": "metupy.utils.globals.get_theme_info",
    "widgets": "metupy.utils.globals.get_widgets",
}

# ═══════════════════════════════════════════════════════
# Content Type Configuration
# ═══════════════════════════════════════════════════════
CONTENT_TYPES = {
    "blog": {
        "enabled": True,
        "prefix": "blog",
        "paginate": 10,
        "rss": True,
        "comments": True,
    },
    "docs": {
        "enabled": True,
        "prefix": "docs",
        "sidebar": True,
        "search": True,
        "versioning": True,
    },
    "slides": {
        "enabled": True,
        "prefix": "slides",
        "theme": "reveal",
        "transition": "slide",
    },
    "landing": {
        "enabled": True,
        "prefix": "",
        "template": "landing.html",
    },
    "resume": {
        "enabled": True,
        "prefix": "resume",
        "template": "resume.html",
    },
    "elearning": {
        "enabled": True,
        "prefix": "learn",
        "tracking": True,
        "quizzes": True,
    },
}

# ═══════════════════════════════════════════════════════
# Pagination Configuration
# ═══════════════════════════════════════════════════════
PAGINATION = {
    "per_page": 10,
    "max_pages": 10,
    "show_first_last": True,
    "show_prev_next": True,
}

# ═══════════════════════════════════════════════════════
# SEO Configuration
# ═══════════════════════════════════════════════════════
SEO = {
    "generate_sitemap": True,
    "generate_robots": True,
    "generate_manifest": True,
    "google_analytics": os.environ.get("GA_TRACKING_ID", ""),
    "google_search_console": os.environ.get("GSC_VERIFICATION", ""),
    "open_graph": {
        "site_name": SITE_NAME,
        "type": "website",
        "image": "/assets/images/og-image.png",
    },
    "twitter": {
        "card": "summary_large_image",
        "site": "@yourtwitter",
    },
}

# ═══════════════════════════════════════════════════════
# Comments Configuration
# ═══════════════════════════════════════════════════════
COMMENTS = {
    "enabled": True,
    "storage": "redis",  # redis, json, database
    "sync_time": "00:00",  # 12 AM
    "moderation": True,
    "spam_protection": True,
    "akismet_key": os.environ.get("AKISMET_KEY", ""),
    "disqus_shortname": os.environ.get("DISQUS_SHORTNAME", ""),
    "gravatar": True,
    "notifications": True,
    "notification_email": os.environ.get("COMMENT_NOTIFY_EMAIL", ""),
}

# ═══════════════════════════════════════════════════════
# Search Configuration
# ═══════════════════════════════════════════════════════
SEARCH = {
    "enabled": True,
    "engine": "lunr",  # lunr, elasticsearch, algolia
    "index_fields": ["title", "content", "tags", "description"],
    "fuzzy": True,
    "highlight": True,
}

# ═══════════════════════════════════════════════════════
# Internationalization (i18n)
# ═══════════════════════════════════════════════════════
LOCALE_DIR = BASE_DIR / "locales"
DEFAULT_LOCALE = "id"
SUPPORTED_LOCALES = ["id", "en"]
TRANSLATIONS_ENABLED = True

# ═══════════════════════════════════════════════════════
# Development/Production Mode
# ═══════════════════════════════════════════════════════
DEBUG = True
TESTING = False
PRODUCTION = False

if os.getenv('METUPY_PRODUCTION', 'false').lower() == 'true':
    DEBUG = False
    TESTING = False
    DEV_LIVE_RELOAD = False
    STUDIO_AUTO_OPEN = False
    CACHE_ENABLED = True
    BUILD_MINIFY_HTML = True
    BUILD_MINIFY_CSS = True
    BUILD_MINIFY_JS = True

# ═══════════════════════════════════════════════════════
# Custom Variables (Add your own below)
# ═══════════════════════════════════════════════════════
CUSTOM_HEADER_SCRIPTS = []
CUSTOM_FOOTER_SCRIPTS = []
CUSTOM_CSS_FILES = []
CUSTOM_JS_FILES = []