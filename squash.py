import argparse
import getpass
import json
import os
import time
from collections import namedtuple
from datetime import datetime, timedelta, date

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

def booking_window():
    today = datetime.today()
    booking_window = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
    print(f"Booking window:{booking_window}")
    return booking_window


def navigate_to_calendar(date, driver):
    url = f"https://clublocker.com/organizations/2270/reservations/{date}/grid"
    try:
        print(f"Attempting to navigate to {url}")
        driver.get(url)
        current_url = driver.current_url
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def navigate_to_matches(driver):
    load_dotenv()
    userid=os.getenv('userid')
    url = f"https://clublocker.com/users/{userid}/matches"
    try:
        print(f"Attempting to navigate to {url}")
        driver.get(url)
        current_url = driver.current_url
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        
@app.route("/reservations", methods=["GET"])
def reservations():
    driver = setup_driver()
    try:
        load_dotenv()
        full_name=os.getenv('full_name')
        days = booking_window()
        bookings = []
        login.login_to_clublocker(driver)
        for day in days:
            navigate_to_calendar(day, driver)
            daily_booking = court.my_reservations(day, full_name, driver)[0]
            if (daily_booking):
                bookings.append(daily_booking)
        bookings_dict = [booking.to_dict() for booking in bookings]
        response = json.dumps(bookings_dict)
        print(response)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        driver.quit()  

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


@app.route("/delete", methods=["DELETE"])
def delete_booking():
    data = request.get_json()
    driver = setup_driver()
    if not data:
        return jsonify({"status": "error", "message": "No bookings provided"}), 400
    try:
        date = parser.parse(data["date"]).strftime("%Y-%m-%d")
        if date:
            load_dotenv()
            full_name=os.getenv('full_name')
            login.login_to_clublocker(driver)
            navigate_to_calendar(date, driver)
            booking = court.delete_booking(date, full_name, driver)
            if booking:
                print(f"Booking status:{booking.status} of booking on {booking.date} at {booking.time} for court {booking.court}")
                response = json.dumps(booking.to_dict())
                return jsonify(response), 200
            else: 
                return jsonify({"status": "error", "message": "slot not found"}), 500
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
        try: 
            date = "2025-10-08"
            load_dotenv()
            full_name=os.getenv('full_name')
            login.login_to_clublocker(driver)
            navigate_to_calendar(date, driver)
            booking = court.delete_booking(date, full_name, driver)
            if booking:
                print(f"Booking status:{booking.status} of booking on {booking.date} at {booking.time} for court {booking.court}")
            else:
                print(f"Error: no slot found")
        except Exception as e:
            print(f"{e}")
        input("Press any key")
        
       
            


if __name__ == "__main__":
    main()


"""
1. Make deletion handling robust to errors and toast warnings
2. Shift to app routing
3. Return 500 error if no slot found
4. Return 200 JSON if booking found
---
5. Make sure ChatGPT always Deletes before creating a new booking if I make a Modify request
"""