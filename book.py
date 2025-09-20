import json
import os
import time
from datetime import datetime

import parsedatetime
from dateutil import parser
from dotenv import load_dotenv

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class ToastError(Exception):
    """Custom exception for toast-related errors"""

    def __init__(self, message, toast_text=None):
        super().__init__(message)
        self.toast_text = toast_text


class BookingListener:
    def __init__(self, driver):
        self.driver = driver
        self.toast_history = []

    def confirm(self, timeout=2):
        """Wait for toast containing specific text"""
        selector = ".mat-simple-snack-bar-content"
        expected_options = [
            "There are empty spots",
            "maximum",
            "too far ahead",
            "back-to-back",
        ]

        try:
            toast = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            for expected_text in expected_options:
                if expected_text.lower() in toast.text.lower():
                    # Raise custom error when toast is found
                    raise ToastError(
                        f"Booking failed: {toast.text}", toast_text=toast.text
                    )
            # If we get here, toast was found but didn't match expected error text
            print(f"Warning! new toast found: {toast.text}")
            return None
        except TimeoutException:
            # No toast found within timeout - this is good (no error)
            return None


def parse_time(text):
    try:
        start_time = datetime.strptime(text, "%I:%M %p").time()
        return start_time
    except:
        return None


def parse_slot_time(separator, text):
    if separator in text.lower():
        parts = text.lower().split(separator, 1)
        if len(parts) == 2:
            return parse_time(parts[0])


def find_slots(booking, driver):
    booking_time = parser.parse(booking.time)

    print(f"Booking time: {booking_time.strftime("%-I:%M %p")} on {booking.date}")
    try:
        columns = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".column.slots"))
        )
        columns.pop()
        elements = []
        for column in columns:
            try:
                slots = column.find_elements(By.CSS_SELECTOR, ".slot.open:not(.past)")
                for slot in slots:
                    elements.append(slot)
            except Exception as e:
                print(f"An error occurred: {str(e.message)}")
                return None
        for element in elements:
            start_time = parse_slot_time(" - ", element.get_attribute("title"))
            ##print(f"start_time: {start_time.strftime('%H:%M %p')}")
            if start_time.strftime("%-I:%M %p") == booking_time.strftime("%-I:%M %p"):
                return element
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


def reserve_slot(driver, element):
    wait = WebDriverWait(driver, 10)
    element.click()
    try:
        modal = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "[role='dialog'], .mat-dialog-container")
            )
        )
        book_prime_time(modal, driver)

        booking_listener = BookingListener(driver)
        button = wait.until(
            lambda driver: modal.find_element(
                By.CSS_SELECTOR, "button.mat-raised-button"
            )
        )
        button.click()
        try:
            status = booking_listener.confirm()
            return True, "Booking Confirmed"
        except ToastError as e:
            return False, e.toast_text
        except Exception as e:
            if e.__class__.__name__ == "TimeoutException":
                return True, "Booking successful"
            else:
                print(f"Rats! Unexpected error: {e}")
                return False, str(e)
    except Exception as e:
        return False, str(e)


def check_prime_time(surface, driver):
    wait = WebDriverWait(driver, 3)
    try:
        prime_time = wait.until(
            lambda driver: surface.find_element(By.CSS_SELECTOR, ".usq-prime-time")
        )
        return prime_time
    except:
        return False


def book_prime_time(modal, driver):
    load_dotenv()
    partner_name = os.getenv("partner_name")
    wait = WebDriverWait(driver, 10)
    if check_prime_time(modal, driver):
        try:
            player_input = wait.until(
                lambda driver: modal.find_element(
                    By.CSS_SELECTOR, 'input.mat-input-element:not([readonly="true"])'
                )
            )
            player_input.clear()
            player_input.send_keys(partner_name)
            x_path = f'//span[contains(text(), "{partner_name}")]'
            dropdown = wait.until(
                lambda driver: player_input.find_element(By.XPATH, x_path)
            )
            if dropdown:
                dropdown.click()
            return True
        except Exception as error:
            print(f"Error type: {type(error).__name__}")
            return False
    else:
        return True
