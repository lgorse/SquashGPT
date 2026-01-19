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
import gpt
import perf_logger
from session_manager import SessionManager

import parsedatetime
from dateutil import parser

from dotenv import load_dotenv

from flask import Flask, jsonify, request

from seleniumbase import Driver



app = Flask(__name__)

# Initialize session manager on app startup
session_mgr = SessionManager.get_instance()

@app.teardown_appcontext
def cleanup_session(exception=None):
    """Cleanup session on Flask app context teardown"""
    if exception:
        print(f"App context ended with exception: {exception}")
    # Session manager has its own atexit cleanup, but we can also clean up here
    # if we want to be more explicit about Flask lifecycle



def setup_driver(mode=None):
    start_time = perf_logger.log_perf_start("setup_driver")
    print(f"Setting up Chrome WebDriver with SeleniumBase UC Mode {mode}")

    headless = not mode == "browser"

    # Build chromium arguments list
    chromium_args = []
    chromium_args.append("--disable-dev-shm-usage")
    chromium_args.append("--enable-logging")
    chromium_args.append("--enable-javascript")
    # Force Chrome to not use any user data directory
    chromium_args.append("--no-first-run")
    chromium_args.append("--no-default-browser-check")
    chromium_args.append("--disable-default-apps")
    chromium_args.append("--disable-extensions")

    # Memory optimization (CRITICAL for Railway)
    chromium_args.append("--memory-pressure-off")
    chromium_args.append("--max_old_space_size=2048")
    chromium_args.append("--no-zygote")
    chromium_args.append("--disable-background-timer-throttling")
    chromium_args.append("--disable-backgrounding-occluded-windows")
    chromium_args.append("--disable-renderer-backgrounding")

    # Additional bot detection evasion
    chromium_args.append("--disable-blink-features=AutomationControlled")

    # Use SeleniumBase Driver with UC mode for better Cloudflare evasion
    driver = Driver(
        uc=True,  # Enable undetected mode (uses undetected-chromedriver internally)
        headless=headless,
        log_cdp=False,
        no_sandbox=True,
        disable_gpu=True,
        incognito=False,
        chromium_arg=",".join(chromium_args)
    )

    perf_logger.log_perf_end("setup_driver", start_time)
    return driver

def booking_window():
    today = datetime.today()
    booking_window = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
    print(f"Booking window:{booking_window}")
    return booking_window


def navigate_to_calendar(date, driver):
    start_time = perf_logger.log_perf_start("navigate_to_calendar", f"date={date}")
    url = f"https://clublocker.com/organizations/2270/reservations/{date}/grid"
    try:
        print(f"Attempting to navigate to {url}")
        driver.get(url)
        current_url = driver.current_url
        perf_logger.log_perf_end("navigate_to_calendar", start_time)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        perf_logger.log_perf_end("navigate_to_calendar", start_time)

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
    start_time = perf_logger.log_perf_start("API:/reservations")
    try:
        bookings = court.my_reservations()
        print(f"the booking {bookings}")
        response = json.dumps(bookings)
        print(response)
        perf_logger.log_perf_end("API:/reservations", start_time)
        return jsonify(response), 200
    except Exception as e:
        perf_logger.log_perf_end("API:/reservations", start_time)
        return jsonify({"status": "error", "message": str(e)}), 500
   

@app.route("/book-courts", methods=["GET", "POST"])
def book_courts():
    start_time = perf_logger.log_perf_start("API:/book-courts")
    data = request.get_json()
    response, status = court.book_courts(data)
    perf_logger.log_perf_end("API:/book-courts", start_time)
    return jsonify(response), status
   


@app.route("/booking/delete", methods=["DELETE", "POST"])
def delete_booking():
    start_time = perf_logger.log_perf_start("API:/booking/delete")
    data = request.get_json()
    response, status = court.delete_booking(data)
    perf_logger.log_perf_end("API:/booking/delete", start_time)
    return jsonify(response), status
   
    

@app.route("/chat", methods=["POST"])
def chat():
   start_time = perf_logger.log_perf_start("API:/chat")
   data = request.get_json()
   perf_logger.log_perf("API:/chat", f"user_id={data.get('user_id')}")
   return gpt.stream(request)

@app.route('/clear', methods=['POST'])
def clear():
    return gpt.clear_chat(request)


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
            date = "2026-01-19"
            load_dotenv()
            full_name=os.getenv('full_name')
            login.login_to_clublocker(driver)
            navigate_to_calendar(date, driver)
            response, status_code = court.delete_booking({"date":date})
            print(f"Response: {response}, Status: {status_code}")
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