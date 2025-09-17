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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Booking:
    def __init__(self, date, time, status=None):
        self.date = date
        self.time = time
        self.status = status


def setup_driver():
    """Set up Chrome WebDriver with basic options"""
    chrome_options = Options()
    # Uncomment the line below to run in headless mode
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--enable-logging")
    chrome_options.set_capability(
        "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
    )
    ##chrome_options.add_argument('--headless')

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


def main():
    print("ClubLocker Booking Automation")
    print("=" * 30)

    bookings = [
        Booking("2025-09-16", "4:30 pm", None),
        Booking("2025-09-17", "5:15 pm", None),
        Booking("2025-09-18", "9:00 am", None),
    ]
    # Get credentials securely
    load_dotenv()
    username = os.getenv("username")
    password = os.getenv("password")

    driver = setup_driver()

    # Attempt login
    login.login_to_clublocker(username, password, driver)

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


if __name__ == "__main__":
    main()


"""
* Update main core so we separate out the key function
* Enable JSON ingestion
* create API wrapper
* create Ngrok wrapper so I can call the API remotely
* instruct Custom GPT
"""
