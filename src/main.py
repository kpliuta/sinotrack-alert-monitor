"""
Entry point for the Sinotrack Alert Monitor web scraper.
"""
import os
from datetime import datetime
from typing import Dict, Any, Optional

from selenium.webdriver.common.by import By

from config import (
    SINOTRACK_ACCOUNT,
    SINOTRACK_PASSWORD,
    SPEED_THRESHOLD,
    GEOFENCE_THRESHOLD_METERS,
    LINK_TEXT_EXCEPTIONS,
    ALARM_TEXT_EXCEPTIONS,
    LATITUDE_TEXT_EXCEPTIONS,
    LONGITUDE_TEXT_EXCEPTIONS,
    TELEGRAM_API_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    SCRAPER_OUTPUT_DIR
)
from framework.error_hook import ScreenshotErrorHook, NotificationErrorHook
from framework.helpers import get_element, send_keys, random_sleep
from framework.notifier import TelegramNotifier
from framework.scraper_builder import ScraperBuilder
from state import init_state, save_state
from utils import safe_int, haversine

# TODO: tidy up
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

    # TODO: is it really needed?
    # # An additional script to ensure the webdriver flag is hidden.
    # self._driver.execute_script("""
    #     Object.defineProperty(navigator, 'webdriver', {
    #         get: () => undefined
    #     });
    # """)

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
        .build()
    ).run()

    scraper.run()


def login_step(driver, state, notify) -> None:
    """
    Handles the login process on the Sinotrack website.

    This step navigates to the login page, selects the server, enters credentials,
    agrees to terms, and clicks the login button.
    """
    driver.get('https://pro.sinotrack.com')
    random_sleep(1000, 2000)

    # Server selection
    get_element(driver, (By.XPATH,
                         "//label[normalize-space(text())='Server']/following-sibling::div//span[normalize-space(text())='Auto select']"),
                60).click()
    random_sleep(1000, 2000)
    get_element(driver, (By.XPATH,
                         "//div[normalize-space(text())='Server cluster']/following-sibling::ul//li[normalize-space(text())='Server 6 | Pro.SinoTrack']"),
                60).click()
    random_sleep(1000, 2000)

    # Credentials
    send_keys(driver, (By.XPATH, "//label[normalize-space(text())='Account']/following-sibling::div//input"),
              SINOTRACK_ACCOUNT, 60)
    random_sleep(1000, 2000)
    send_keys(driver, (By.XPATH, "//label[normalize-space(text())='Password']/following-sibling::div//input"),
              SINOTRACK_PASSWORD, 60)
    random_sleep(1000, 2000)

    # Agreement and login
    get_element(driver, (By.CLASS_NAME, "ivu-checkbox"), 60).click()
    random_sleep(1000, 2000)
    get_element(driver, (By.XPATH, "//button[span[normalize-space(text())='Login']]"), 60).click()
    random_sleep(2000, 4000)  # Wait a bit longer for the map to load


def extract_data_step(driver, state, notify):
    """
    Selects the device and extracts vehicle data from the Sinotrack platform.

    This step navigates to the device list, selects a specific device (hardcoded for now),
    expands the position section, and extracts various data points like link status, speed,
    alarm state, latitude, and longitude.
    """
    get_element(driver, (By.XPATH,
                         "//div[contains(@class, 'DeviceList')]//div[@class='CarNum' and normalize-space(text())='9176369853']"),
                60).click()
    random_sleep(1000, 2000)
    get_element(driver, (By.XPATH,
                         "//div[contains(@class, 'RealDataPanel')]//div[@class='ivu-collapse-item']//div[text()='Position']"),
                60).click()
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

    return {
        'link': link_text,
        'speed': speed_text,
        'alarm': alarm_text,
        'latitude': latitude_text,
        'longitude': longitude_text,
    }


def process_data_step(driver, state, notify):
    """
    Processes the extracted vehicle data and sends notifications based on defined thresholds.

    This step checks the link status, speed, alarm state, and geofence distance.
    If any thresholds are exceeded or conditions are met, a notification is sent.
    It also handles saving the initial geolocation for geofencing if not already present.
    """
    # Check link status
    link_text: str = state.get('link', '')
    if "Online" not in link_text and link_text not in LINK_TEXT_EXCEPTIONS:
        notify(f"Sinotrack-Checker: Link is {link_text}")

    # Check speed
    speed_text: str = state.get('speed', '')
    if safe_int(speed_text, 0) > SPEED_THRESHOLD:
        notify(f"Sinotrack-Checker: Speed is {speed_text}, which is more than {SPEED_THRESHOLD}")

    # Check alarm
    alarm_text: str = state.get('alarm', '')
    if alarm_text and alarm_text not in ALARM_TEXT_EXCEPTIONS:
        notify(f"Sinotrack-Checker: Alarm State is {alarm_text}")

    # Check distance from geofence
    latitude_text: str = state.get('latitude', '')
    longitude_text: str = state.get('longitude', '')
    if (
            latitude_text and longitude_text
            and latitude_text not in LATITUDE_TEXT_EXCEPTIONS
            and longitude_text not in LONGITUDE_TEXT_EXCEPTIONS
    ):
        geofence: Dict[str, Any] = state.get('geofence', {})
        init_latitude: Optional[float] = geofence.get('startup_latitude')
        init_longitude: Optional[float] = geofence.get('startup_longitude')

        if init_latitude and init_longitude:
            latitude: float = float(latitude_text)
            longitude: float = float(longitude_text)
            distance: int = int(haversine(init_latitude, init_longitude, latitude, longitude))
            print(f"Distance: {distance}m")
            if distance > GEOFENCE_THRESHOLD_METERS:
                notify(f"Sinotrack-Checker: Distance: {distance}m, which is more than {GEOFENCE_THRESHOLD_METERS}m")
        else:
            print("Saving initial geolocation for geofence.")
            state['geofence'] = {
                'startup_latitude': float(latitude_text),
                'startup_longitude': float(longitude_text),
            }
            save_state(state)  # Persist the new geofence data


if __name__ == "__main__":
    main()
