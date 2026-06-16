import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# API Keys and Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Logging configuration
LOG_FILE_PATH = LOGS_DIR / "business_pilot.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("business_pilot")

# Default Lead Scoring Parameters
SCORING_RULES = {
    # Revenue brackets (USD) and their assigned weight/points
    "revenue_brackets": [
        {"min": 100000000, "points": 40},  # $100M+
        {"min": 10000000, "points": 30},   # $10M - $100M
        {"min": 1000000, "points": 20},    # $1M - $10M
        {"min": 0, "points": 10}            # Under $1M
    ],
    # Employee size points
    "employee_brackets": [
        {"min": 1000, "points": 20},
        {"min": 100, "points": 15},
        {"min": 10, "points": 10},
        {"min": 0, "points": 5}
    ],
    # Interaction weight multiplier (number of interactions * points)
    "interaction_factor": 3.0,
    # Interest score weight (0.0 - 1.0)
    "conversion_rate_weight": 20.0
}

# Tiers threshold for final lead categorisation
PRIORITY_TIERS = {
    "Hot": 70,    # score >= 70
    "Warm": 40,   # score >= 40 and < 70
    "Cold": 0     # score < 40
}

# Industry Benchmarks for analysis comparison
INDUSTRY_BENCHMARKS = {
    "SaaS": {
        "average_conversion_rate": 0.25,
        "market_growth": 0.18,
        "high_value_revenue_threshold": 10000000
    },
    "Healthcare": {
        "average_conversion_rate": 0.35,
        "market_growth": 0.12,
        "high_value_revenue_threshold": 25000000
    },
    "Finance": {
        "average_conversion_rate": 0.40,
        "market_growth": 0.08,
        "high_value_revenue_threshold": 50000000
    },
    "E-commerce": {
        "average_conversion_rate": 0.15,
        "market_growth": 0.22,
        "high_value_revenue_threshold": 5000000
    },
    "Manufacturing": {
        "average_conversion_rate": 0.20,
        "market_growth": 0.05,
        "high_value_revenue_threshold": 30000000
    },
    "Education": {
        "average_conversion_rate": 0.18,
        "market_growth": 0.10,
        "high_value_revenue_threshold": 2000000
    }
}
