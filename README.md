# Sinotrack Alert Monitor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A web scraper that monitors a [Sinotrack](https://pro.sinotrack.com/) vehicle tracker and sends alerts via Telegram for events like speeding, geofence breaches, and offline status.

This script is designed to be run in two primary environments:
1.  On an Android device using **Termux** and the `termux-web-scraper` framework.
2.  On a standard desktop environment as a Python Selenium script.

[The Droid You're Looking For: Scraping Websites on Android with Termux](https://kpliuta.github.io/blog/posts/scraping-websites-on-android-with-termux/)

## Features

*   **Speed Monitoring:** Sends an alert if the vehicle exceeds a predefined speed limit.
*   **Geofence Monitoring:** Sends an alert if the vehicle moves beyond a specified distance from its initial location.
*   **Device Status Monitoring:** Sends an alert if the tracker goes offline.
*   **Alarm Monitoring:** Sends an alert if the device reports an alarm state.
*   **Telegram Notifications:** Uses a Telegram bot to send real-time alerts.
*   **Flexible Deployment:** Can be run on Android (via Termux) or on a desktop machine.
*   **Configurable:** All thresholds, credentials, and alerts can be set via a `.env` file.
*   **Resilient:** Built on the `termux-web-scraper` framework, it handles errors and can run in a continuous loop.

## How it Works

The scraper uses Selenium to log into the Sinotrack web interface, and extract the vehicle's real-time data.

1.  **Login:** The script navigates to `pro.sinotrack.com` and logs in with your account credentials.
2.  **Data Extraction:** It selects your device and scrapes data points like speed, GPS coordinates, and connection status.
3.  **Data Processing:** The extracted data is processed to check against the configured thresholds (speed, geofence).
4.  **Alerting:** If any rules are triggered, a notification is sent to your specified Telegram chat.
5.  **State Management:** The script maintains a state file (`state.yaml`) to track information between runs, such as the initial location for the geofence.

## Prerequisites

Before you can use the Termux Web Scraper, you need to have the following installed on your Android device:

*   **Termux:** You can download Termux from the [F-Droid](https://f-droid.org/en/packages/com.termux/) or [Google Play](https://play.google.com/store/apps/details?id=com.termux) store.
*   **Git:** You can install Git in Termux by running `pkg install git`.

You also need to:

*   **Disable Battery Optimization:** Disable battery optimization for Termux to prevent it from being killed by the Android system.
*   **Acquire a Wakelock:** Acquire a wakelock in Termux to prevent the device from sleeping while your scraper is running.
*   **Address Phantom Process Killing (Android 12+):** On Android 12 and newer, you may need to disable phantom process killing to prevent Termux from being killed. You can do this by running the following command in an ADB shell:
    ```bash
    ./adb shell "settings put global settings_enable_monitor_phantom_procs false"
    ```
    
## Getting Started

### Termux Environment
1.  Get started by launching Termux on your Android device and cloning the repository:
    ```bash
    git clone https://github.com/kpliuta/sinotrack-alert-monitor.git
    ```

2.  Then, navigate to a project and edit `.env` with your credentials and settings:
    ```bash
    cd sinotrack-alert-monitor
    nano .env
    ```

3.  Finally, start the runner script:
    ```bash
    ./termux-runner.sh
    ```
    
### Desktop Environment
To run the scraper on a desktop machine, simply execute the `main.py` script, specifying unique ID for the session:
```bash
SCRAPER_SESSION_ID=session_id poetry run python src/main.py
```

## Configuration

The following environment variables must be set in the `.env` file:

### Core Configuration
*   `SCRAPER_OUTPUT_DIR`: Absolute path to a directory for storing state files and screenshots.
*   `TELEGRAM_API_URL`: The Telegram Bot API URL (default: `https://api.telegram.org`).
*   `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.
*   `TELEGRAM_CHAT_ID`: The ID of the Telegram chat where alerts will be sent.
*   `SINOTRACK_ACCOUNT`: Your Sinotrack account username.
*   `SINOTRACK_PASSWORD`: Your Sinotrack account password.
*   `SINOTRACK_DEVICE_ID`: The device identifier for the vehicle you want to monitor.

### Thresholds
*   `SPEED_THRESHOLD`: The speed limit in km/h. An alert is sent if this is exceeded (default: `10`).
*   `GEOFENCE_THRESHOLD_METERS`: The geofence radius in meters. An alert is sent if the vehicle moves further than this (default: `500`).

### Alert Switches
You can enable or disable specific alerts by setting the following variables to `true` or `false`:
*   `CHECK_LINK_STATUS_ENABLED`: Monitors if the tracker goes offline (default: `true`).
*   `CHECK_SPEED_ENABLED`: Monitors if the vehicle exceeds the `SPEED_THRESHOLD` (default: `true`).
*   `CHECK_ALARM_ENABLED`: Monitors the device's alarm state (default: `true`).
*   `CHECK_GEOFENCE_ENABLED`: Monitors if the vehicle breaches the `GEOFENCE_THRESHOLD_METERS` (default: `true`).

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue if you have any suggestions or find any bugs.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
