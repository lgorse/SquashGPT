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

from seleniumbase import SB



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

    # Check for local headless override (Mac dev environment)
    load_dotenv()
    force_headless = os.getenv("FORCE_HEADLESS", "false").lower() == "true"

    if force_headless:
        # Local dev: use true headless (may not bypass Cloudflare)
        use_xvfb = False
        use_headless = True
        print(f"DEBUG: FORCE_HEADLESS=true, using headless mode (local dev only)")
    else:
        # Production: use xvfb (virtual display on Linux, visible on Mac)
        use_xvfb = (mode != "browser")
        use_headless = False
        print(f"DEBUG: mode={mode}, use_xvfb={use_xvfb}")

    # Build chromium arguments list
    chromium_args = []
    chromium_args.append("--disable-dev-shm-usage")
    chromium_args.append("--disable-blink-features=AutomationControlled")
    chromium_args.append("--memory-pressure-off")
    chromium_args.append("--max_old_space_size=2048")
    chromium_args.append("--no-zygote")
    chromium_args.append("--disable-background-timer-throttling")
    chromium_args.append("--disable-backgrounding-occluded-windows")
    chromium_args.append("--disable-renderer-backgrounding")

    # Use SB() context manager for UC mode with persistent session
    sb_context = SB(
        uc=True,  # Enable UC mode for Cloudflare bypass
        xvfb=use_xvfb,  # Virtual display (Linux) or visible (Mac)
        headless=use_headless,  # True headless for local dev only
        test=True,  # Keep session open for persistent driver
        chromium_arg=",".join(chromium_args)
    )

    # Enter context to get actual SB instance
    sb = sb_context.__enter__()  # Returns the actual SB instance with methods

    # Store context manager reference for proper cleanup
    sb._sb_context = sb_context

    perf_logger.log_perf_end("setup_driver", start_time)
    return sb  # Return SB instance (has driver as sb.driver)

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
        session_mgr = SessionManager.get_instance()
        driver = session_mgr.get_driver(mode=args.mode)
        try:
            data = {"bookings":
                    [
                        {
                            "date": "2026-06-20",
                            "time": "2:15 pm"
                            }
                    ]
                }
            load_dotenv()
            full_name=os.getenv('full_name')
            response, status_code = court.book_courts(data)
            #response, status_code = court.delete_booking(date)
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