import argparse
import getpass
import json
import os
import time
from collections import namedtuple
from datetime import datetime

import book

# Custom classes
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


class Booking:
    def __init__(self, date, time, status=None):
        self.date = parser.parse(date).strftime("%Y-%m-%d")
        self.time = parser.parse(time).strftime("%-I:%M %p").lower()
        self.status = status

    def to_dict(self):
        return {
            "date": self.date,
            "time": self.time,
            "status": self.status,
        }


def setup_driver():
    """Set up Chrome WebDriver with basic options"""
    chrome_options = Options()
    # Uncomment the line below to run in headless mode
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
        driver.get(url)
        current_url = driver.current_url
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def request_to_bookings(booking_json):
    booking_request = booking_json["bookings"]
    print(booking_request)
    bookings = []
    for request in booking_request:
        booking = Booking(request["date"], request["time"], request["status"])
        bookings.append(booking)
        print(request)
        print(booking.status)

    return bookings


def book_slots(bookings):
    driver = setup_driver()

    # Attempt login
    login.login_to_clublocker(driver)

    for booking in bookings:
        navigate_to_calendar(booking.date, driver)
        slot = book.find_slots(booking, driver)
        booking_status = ()
        if slot:
            booking_status = book.reserve_slot(driver, slot)
        else:
            booking_status = (False, "No slots found")
        print(booking_status[1])
        booking.status = booking_status[1]

    ##summarize booking
    for booking in bookings:
        print(f"Booking on {booking.date} at {booking.time}: {booking.status}")
    return bookings


@app.route("/book-courts", methods=["GET", "POST"])
def book_courts():
    data = request.get_json()
    print(data)
    if not data:
        return jsonify({"status": "error", "message": "No bookings provided"}), 400
    bookings = request_to_bookings(data)
    try:
        confirmations = book_slots(bookings)
        confirmations_dict = [confirmation.to_dict() for confirmation in confirmations]
        response = json.dumps(confirmations_dict)
        print(response)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def main():
    parser = argparse.ArgumentParser(description="Court Booking System")
    parser.add_argument(
        "--mode",
        choices=["flask", "prod", "interactive"],
        default="interactive",
        help="How to run the application",
    )
    args, remaining = parser.parse_known_args()

    if args.mode == "flask":
        app.run(debug=True)
    elif args.mode == "prod":
        port = int(os.environ.get("PORT", 8080))
        app.run(host="0.0.0.0", port=port)
    else:
        json_booking = {
            "bookings": [
                {"date": "September 22 2025", "time": "9:00 am", "status": None},
                {"date": "2025-09-17", "time": "5:15 pm", "status": None},
                {"date": "2025-09-18", "time": "9:00 am", "status": None},
            ]
        }
        bookings = request_to_bookings(json_booking)
        book_slots(bookings)


if __name__ == "__main__":
    main()


"""
* Update main core so we separate out the key function DONE
* Enable JSON ingestion: ingest JSON, convert to Booking objects, DONE
* create API wrapper DONE
* create Ngrok wrapper so I can call the API remotely DONE with Cloudflare
* instruct Custom GPT DONE in development
* Push to production
"""
