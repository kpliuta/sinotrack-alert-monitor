"""
Loads the configuration from the .env file and makes it available to the application.
"""
import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_env_var(name: str, default: Optional[str] = None) -> str:
    """
    Gets an environment variable, raising an error if it's not set and no default is provided.

    Args:
        name: The name of the environment variable.
        default: The default value to return if the environment variable is not set.

    Returns:
        The value of the environment variable.

    Raises:
        ValueError: If the environment variable is not set and no default is provided.
    """
    value = os.getenv(name)
    if value is None:
        if default is not None:
            return default
        raise ValueError(f"Environment variable {name} is not set and no default was provided.")
    return value


# --- Technical & Security Parameters ---

# Scraper session ID
SCRAPER_SESSION_ID: str = get_env_var("SCRAPER_SESSION_ID")

# Output directory for scraper data
SCRAPER_OUTPUT_DIR: str = get_env_var("SCRAPER_OUTPUT_DIR", "/mnt/sinotrack-alert-monitor")

# Telegram API URL
TELEGRAM_API_URL: str = get_env_var("TELEGRAM_API_URL")

# Telegram Bot Token
TELEGRAM_BOT_TOKEN: str = get_env_var("TELEGRAM_BOT_TOKEN")

# Telegram Chat ID
TELEGRAM_CHAT_ID: str = get_env_var("TELEGRAM_CHAT_ID")

# Sinotrack credentials
SINOTRACK_ACCOUNT: str = get_env_var("SINOTRACK_ACCOUNT")
SINOTRACK_PASSWORD: str = get_env_var("SINOTRACK_PASSWORD")
SINOTRACK_DEVICE_ID: str = get_env_var("SINOTRACK_DEVICE_ID")

# Scraper state file
SCRAPER_STATE_FILE: str = os.path.join(SCRAPER_OUTPUT_DIR, "state.yaml")

# TODO: remove if there's no use to it
# User agents for the web driver
USER_AGENTS: list[str] = [
    "Mozilla/5.0 (X11; Linux x86_64; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:110.0) Gecko/20100101 Firefox/110.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11.6; rv:109.0) Gecko/20100101 Firefox/109.0",
]

# --- Scraper Parameters ---

# Speed threshold in km/h
SPEED_THRESHOLD: int = int(get_env_var("SPEED_THRESHOLD", "10"))

# Geofence threshold in meters
GEOFENCE_THRESHOLD_METERS: int = int(get_env_var("GEOFENCE_THRESHOLD_METERS", "500"))

# Sometimes sinotrack returns unusual values and cause false-positive alerts. These filters are used to exclude these cases.
LINK_TEXT_EXCEPTIONS: list[str] = ["-"]
ALARM_TEXT_EXCEPTIONS: list[str] = []
LATITUDE_TEXT_EXCEPTIONS: list[str] = ["-"]
LONGITUDE_TEXT_EXCEPTIONS: list[str] = ["-"]

# TODO: select active checkers
# TODO: select active notifiers
