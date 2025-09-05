"""
Manages the state of the scraper, including loading and saving data to a YAML file.
"""
import os
from typing import Dict, Any
import yaml

from config import SCRAPER_STATE_FILE, SCRAPER_SESSION_ID


def load_state() -> Dict[str, Any]:
    """
    Loads the scraper state from the YAML file.

    If the state file does not exist, it returns an empty dictionary.

    Returns:
        A dictionary representing the application state.
    """
    if not os.path.exists(SCRAPER_STATE_FILE):
        return {}
    with open(SCRAPER_STATE_FILE, 'r') as f:
        return yaml.safe_load(f) or {}


def save_state(state: Dict[str, Any]) -> None:
    """
    Saves the scraper state to the YAML file.

    This function will create the output directory if it does not exist.

    Args:
        state: A dictionary representing the state to be saved.
    """
    os.makedirs(os.path.dirname(SCRAPER_STATE_FILE), exist_ok=True)
    with open(SCRAPER_STATE_FILE, 'w') as f:
        yaml.dump(state, f)


def init_state(startup_time: str) -> Dict[str, Any]:
    """
    Initializes the scraper state for the current run.

    It loads the state from the state file. If the file doesn't exist, or if
    the `SCRAPER_SESSION_ID` has changed since the last run, a new state is
    created. Otherwise, the existing state is used.

    Args:
        startup_time: The startup time of the application, used when creating a new state.

    Returns:
        A dictionary representing the initialized state.
    """
    state = load_state()
    current_session_id = state.get('session_id')

    if not state or current_session_id != SCRAPER_SESSION_ID:
        print(f"Initializing new state for session ${SCRAPER_SESSION_ID}.")
        state = {
            'session_id': SCRAPER_SESSION_ID,
            'startup_time': startup_time,
            'geofence': {},
        }
        save_state(state)
    else:
        print("Continuing with existing state for session ${SCRAPER_SESSION_ID}.")

    return state
