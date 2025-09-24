import argparse
import getpass
import json
import os
import time
from collections import namedtuple
from datetime import datetime

# Custom classes
import court
import login

import parsedatetime
from dateutil import parser

from dotenv import load_dotenv

from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

app = Flask(__name__)


def setup_driver(mode=None):
    print(f"Setting up Chrome WebDrive {mode}")
    chrome_options = Options()
    if not mode == "browser":
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--enable-logging")
    chrome_options.set_capability(
        "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
    )
    chrome_options.add_argument("--enable-javascript")
    # Force Chrome to not use any user data directory
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-extensions")
    ## chrome_options.binary_location = "/usr/bin/google-chrome"

    # Memory optimization (CRITICAL for Railway)
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--max_old_space_size=2048")  # Limit memory
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")

    # Make sure you have ChromeDriver installed and in PATH
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def navigate_to_calendar(date, driver):
    url = f"https://clublocker.com/organizations/2270/reservations/{date}/grid"
    try:
        print(f"Attempting to navigate to {url}")
        driver.get(url)
        current_url = driver.current_url
    except Exception as e:
        print(f"An error occurred: {str(e)}")


@app.route("/book-courts", methods=["GET", "POST"])
def book_courts():
    data = request.get_json()
    driver = setup_driver()
    print(data)
    if not data:
        return jsonify({"status": "error", "message": "No bookings provided"}), 400
    bookings = court.request_to_bookings(data)
    try:
        login.login_to_clublocker(driver)
        confirmations = court.book_slots(bookings, driver)
        confirmations_dict = [confirmation.to_dict() for confirmation in confirmations]
        response = json.dumps(confirmations_dict)
        print(response)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(description="Court Booking System")
    parser.add_argument(
        "--mode",
        choices=["flask", "prod", "interactive", "browser"],
        help="How to run the application",
    )
    args, remaining = parser.parse_known_args()

    if args.mode == "flask":
        app.run(debug=True)
    elif args.mode == "prod":
        port = int(os.environ.get("PORT", 8080))
        app.run(host="0.0.0.0", port=port)
    else:
        driver = setup_driver(args.mode)
        json_booking = {
            "bookings": [
                {"date": "September 25 2025", "time": "6:00 pm", "status": None},
            ]
        }
        try:
            bookings = court.request_to_bookings(json_booking)
            login.login_to_clublocker(driver)
            court.book_slots(bookings, driver)
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    main()
