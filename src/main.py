"""
Entry point for the Sinotrack Alert Monitor web scraper.
"""
import os
from datetime import datetime
from typing import Dict, Any

from selenium.webdriver.common.by import By
from termux_web_scraper.error_hook import ScreenshotErrorHook, NotificationErrorHook
from termux_web_scraper.helpers import click_element
from termux_web_scraper.helpers import get_element, send_keys, random_sleep
from termux_web_scraper.notifier import TelegramNotifier
from termux_web_scraper.scraper_builder import ScraperBuilder

from config import (
    SINOTRACK_ACCOUNT,
    SINOTRACK_PASSWORD,
    SINOTRACK_DEVICE_ID,
    SPEED_THRESHOLD,
    GEOFENCE_THRESHOLD_METERS,
    LINK_TEXT_EXCEPTIONS,
    ALARM_TEXT_EXCEPTIONS,
    LATITUDE_TEXT_EXCEPTIONS,
    LONGITUDE_TEXT_EXCEPTIONS,
    TELEGRAM_API_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    SCRAPER_OUTPUT_DIR,
    CHECK_LINK_STATUS_ENABLED,
    CHECK_SPEED_ENABLED,
    CHECK_ALARM_ENABLED,
    CHECK_GEOFENCE_ENABLED
)
from state import init_state, save_state
from utils import safe_int, haversine


def main() -> None:
    """
    Main function to run the Sinotrack alert monitor.

    This function initializes the application state, configures the scraper with
    defined steps and error hooks, and then runs the scraping process.
    """
    startup_time: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Starting up at: {startup_time}")

    # Initialize the application state
    state: Dict[str, Any] = init_state(startup_time)

    # Build and run the application using the framework
    scraper = (
        ScraperBuilder()
        .with_state(state)
        .with_notifier(
            TelegramNotifier(
                api_url=TELEGRAM_API_URL,
                bot_token=TELEGRAM_BOT_TOKEN,
                chat_id=TELEGRAM_CHAT_ID
            ))
        .with_error_hook(ScreenshotErrorHook(os.path.join(SCRAPER_OUTPUT_DIR, "screenshots")))
        .with_error_hook(NotificationErrorHook())
        .with_step("Login", login_step)
        .with_step("Extract Data", extract_data_step)
        .with_step("Process Data", process_data_step)
        .with_step("Update Session State", update_session_state)
        .build()
    )

    scraper.run()


def login_step(driver, state, notify):
    """
    Handles the login process on the Sinotrack website.

    This step navigates to the login page, selects the server, enters credentials,
    agrees to terms, and clicks the login button.
    """
    driver.get('https://pro.sinotrack.com')
    random_sleep(1000, 2000)

    # Server selection
    click_element(driver, (By.XPATH,
                           "//label[normalize-space(text())='Server']/following-sibling::div//span[normalize-space(text())='Auto select']"),
                  60)
    random_sleep(1000, 2000)
    click_element(driver, (By.XPATH,
                           "//div[normalize-space(text())='Server cluster']/following-sibling::ul//li[normalize-space(text())='Server 6 | Pro.SinoTrack']"),
                  60)
    random_sleep(1000, 2000)

    # Credentials
    send_keys(driver, (By.XPATH, "//label[normalize-space(text())='Account']/following-sibling::div//input"),
              SINOTRACK_ACCOUNT, 60)
    random_sleep(1000, 2000)
    send_keys(driver, (By.XPATH, "//label[normalize-space(text())='Password']/following-sibling::div//input"),
              SINOTRACK_PASSWORD, 60)
    random_sleep(1000, 2000)

    # Agreement and login
    click_element(driver, (By.CLASS_NAME, "ivu-checkbox"), 60)
    random_sleep(1000, 2000)
    click_element(driver, (By.XPATH, "//button[span[normalize-space(text())='Login']]"), 60)


def extract_data_step(driver, state, notify):
    """
    Selects the device and extracts vehicle data from the Sinotrack platform.

    This step navigates to the device list, selects a specific device (hardcoded for now),
    expands the position section, and extracts various data points like link status, speed,
    alarm state, latitude, and longitude.
    """
    click_element(driver, (By.XPATH,
                           f"//div[contains(@class, 'DeviceList')]//div[@class='CarNum' and normalize-space(text())='{SINOTRACK_DEVICE_ID}']"),
                  60)
    random_sleep(1000, 2000)
    click_element(driver, (By.XPATH,
                           "//div[contains(@class, 'RealDataPanel')]//div[@class='ivu-collapse-item']//div[text()='Position']"),
                  60)
    random_sleep(1000, 2000)

    link_text = get_element(driver, (By.XPATH,
                                     "//table[contains(@class, 'PosCard')]//th[div='Link']/ancestor::table/tr[2]/td[1]/span[1]"),
                            60).text.strip()
    speed_text = get_element(driver, (By.XPATH,
                                      "//table[contains(@class, 'PosCard')]//th[div='Speed']/ancestor::table/tr[2]/td[2]/span[1]"),
                             60).text.strip()
    alarm_text = get_element(driver, (By.XPATH,
                                      "//table[contains(@class, 'PosCard')]//div[contains(text(), 'Alarm state')]/ancestor::tr/td[@class='State']"),
                             60).text.strip()
    latitude_text = get_element(driver, (By.XPATH,
                                         "//table[contains(@class, 'PosCard')]//div[contains(text(), 'Latitude')]/ancestor::tr/td[@class='State']"),
                                60).text.strip()
    longitude_text = get_element(driver, (By.XPATH,
                                          "//table[contains(@class, 'PosCard')]//div[contains(text(), 'Longitude')]/ancestor::tr/td[@class='State']"),
                                 60).text.strip()

    extracted_data: Dict[str, str] = {
        'link_text': link_text,
        'speed_text': speed_text,
        'alarm_text': alarm_text,
        'latitude_text': latitude_text,
        'longitude_text': longitude_text,
    }
    print(f"Extracted data: {extracted_data}")

    state.update({'last_run': extracted_data})


def process_data_step(driver, state, notify):
    """
    Processes the extracted vehicle data and sends notifications based on defined thresholds.

    This step checks the link status, speed, alarm state, and geofence distance.
    If any thresholds are exceeded or conditions are met, a notification is sent.
    It also handles saving the initial geolocation for geofencing if not already present.
    """
    last_run: Dict[str, Any] = state.get('last_run', {})

    # Check link status
    if CHECK_LINK_STATUS_ENABLED:
        link_text = last_run.get('link_text')
        if "Online" not in link_text and link_text not in LINK_TEXT_EXCEPTIONS:
            notify(f"Sinotrack-Checker: Link is {link_text}")

    # Check speed
    if CHECK_SPEED_ENABLED:
        speed_text = last_run.get('speed_text')
        if safe_int(speed_text, 0) > SPEED_THRESHOLD:
            notify(f"Sinotrack-Checker: Speed is {speed_text}, which is more than {SPEED_THRESHOLD}")

    # Check alarm
    if CHECK_ALARM_ENABLED:
        alarm_text = last_run.get('alarm_text')
        if alarm_text and alarm_text not in ALARM_TEXT_EXCEPTIONS:
            notify(f"Sinotrack-Checker: Alarm State is {alarm_text}")

    # Check distance from geofence
    if CHECK_GEOFENCE_ENABLED:
        latitude_text = last_run.get('latitude_text')
        longitude_text = last_run.get('longitude_text')
        if (
                latitude_text and longitude_text
                and latitude_text not in LATITUDE_TEXT_EXCEPTIONS
                and longitude_text not in LONGITUDE_TEXT_EXCEPTIONS
        ):
            geofence: Dict[str, Any] = state.get('geofence', {})
            startup_latitude = geofence.get('startup_latitude')
            startup_longitude = geofence.get('startup_longitude')

            latitude = float(latitude_text)
            longitude = float(longitude_text)

            if startup_latitude and startup_longitude:
                # Calculate geofence distance if startup_latitude and startup_longitude are set
                print(f"Startup latitude: {startup_latitude}. Startup longitude: {startup_longitude}")
                distance = int(haversine(startup_latitude, startup_longitude, latitude, longitude))
                print(f"Geofence distance: {distance}m")
                if distance > GEOFENCE_THRESHOLD_METERS:
                    notify(
                        f"Sinotrack-Checker: Geofence distance: {distance}m, which is more than {GEOFENCE_THRESHOLD_METERS}m")
            else:
                # Update startup_latitude and startup_longitude if it's a new run
                print("Update startup_latitude and startup_longitude for geofence.")
                state.update({
                    'geofence': {
                        'startup_latitude': latitude,
                        'startup_longitude': longitude,
                    }
                })


def update_session_state(driver, state, notify):
    save_state(state)


if __name__ == "__main__":
    main()
