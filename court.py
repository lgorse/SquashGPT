import json
import os
import time
from datetime import datetime
import traceback

import parsedatetime

import squash
from dateutil import parser
from dotenv import load_dotenv
import re
import login

from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Booking:
    def __init__(self, date, time, status=None, court=None):
        self.date = parser.parse(date).strftime("%Y-%m-%d")
        self.time = parser.parse(time).strftime("%-I:%M %p").lower()
        self.status = status
        self.court = self.extract_number(court)

    def to_dict(self):
        return {
            "date": self.date,
            "time": self.time,
            "status": self.status,
            "court": self.court
        }
    
    def extract_number(self, text):
        if text:
            match = re.search(r'-?\d+\.?\d*', text)
            if match:
                num_str = match.group()
                return int(num_str)
        return None




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
            "does not allow",
            "cannot enter a score",
            "4 hours before it is scheduled"
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

    print(f'Booking time: {booking_time.strftime("%-I:%M %p")} on {booking.date}')
    try:
        columns = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".column.slots"))
        )
        print(f"column length: {len(columns)}")
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
            if start_time.strftime("%-I:%M %p") == booking_time.strftime("%-I:%M %p"):
                return element
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


def reserve_slot(driver, element):
    wait = WebDriverWait(driver, 10)
    driver.execute_script("arguments[0].click();", element)
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
        driver.execute_script("arguments[0].click();", button)
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
                # dropdown.click()
                driver.execute_script("arguments[0].click();", dropdown)
            return True
        except Exception as error:
            print(f"Error type: {type(error).__name__}")
            return False
    else:
        return True


def request_to_bookings(booking_json):
    booking_request = booking_json["bookings"]
    print(f"the booking request{booking_request}")
    bookings = []
    for request in booking_request:
        booking = Booking(request.get("date"), request.get("time"), request.get("status"))
        bookings.append(booking)
        print(request)
        print(booking.status)
    return bookings


def book_slots(bookings, driver):
    print("booking slots")
    for booking in bookings:
        squash.navigate_to_calendar(booking.date, driver)
        slot = find_slots(booking, driver)
        booking_status = ()
        if slot:
            booking_status = reserve_slot(driver, slot)
        else:
            booking_status = (False, "No slots found")
        print(booking_status[1])
        booking.status = booking_status[1]

    ##summarize booking
    for booking in bookings:
        print(f"Booking on {booking.date} at {booking.time}: {booking.status}")
    return bookings

def book_courts(data):
    driver = squash.setup_driver()
    print(f"booking{data}")
    bookings = request_to_bookings(data)
    print(f"the data {bookings}")
    try:
        login.login_to_clublocker(driver)
        confirmations = book_slots(bookings, driver)
        confirmations_dict = [confirmation.to_dict() for confirmation in confirmations]
        response = json.dumps(confirmations_dict)
        print(response)
        return response, 200
    except Exception as e:
        return ({"status": "error", "message": str(e)}), 500
    finally:
        driver.quit()

def my_reservations():
    driver = squash.setup_driver()
    try:
        load_dotenv()
        full_name=os.getenv('full_name')
        days = squash.booking_window()
        bookings = []
        login.login_to_clublocker(driver)
        for day in days:
            squash.navigate_to_calendar(day, driver)
            daily_booking = day_reservation(day, full_name, driver)[0]
            if (daily_booking):
                bookings.append(daily_booking)
        bookings_dict = [booking.to_dict() for booking in bookings]
        return bookings_dict
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        driver.quit() 


def day_reservation(date, name, driver):
    try:
        columns = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".column.slots"))
        )
        columns.pop()
        for index, column in enumerate(columns):
            col_num = index+1
            try:
                slots = column.find_elements(By.CSS_SELECTOR, ".slot.match")
                for slot in slots:
                    title = slot.get_attribute("title")
                    if title and name in title:
                        start_time = parse_slot_time(" - ", title)
                        booking = Booking(date, start_time.strftime('%I:%M %p'), None, str(col_num))
                        print(f"Found a booking on {booking.date} at {booking.time} on Court {booking.court}")
                        return booking, slot
            except TimeoutException as e:
                print("No slot found")
            except NoSuchElementException as e:
                print(f"An  error occurred: {str(e)}")
        return None, None
    except Exception as e:
        print(f"Error:{e}")


def delete_booking(data):
    date = parser.parse(data.get("date")).strftime("%Y-%m-%d")
    if date:
        try:
            driver = squash.setup_driver()
            load_dotenv()
            full_name=os.getenv('full_name')
            login.login_to_clublocker(driver)
            squash.navigate_to_calendar(date, driver)
            booking, slot = day_reservation(date, full_name, driver)
            wait = WebDriverWait(driver, 5)
            if slot:
                status, message = delete_slot(driver, slot)
                booking.status = message
            if booking:
                print(f"Booking status:{booking.status} of booking on {booking.date} at {booking.time} for court {booking.court}")
                response = json.dumps(booking.to_dict())
                return response, 200
            else: 
                return ({"status": "error", "message": "slot not found"}), 500
        except Exception as e:
            return ({"status": "error", "message": str(e)}), 500
        finally:
            driver.quit()
        


def delete_slot(driver, slot):
    wait = WebDriverWait(driver, 5)
    driver.execute_script("arguments[0].click();", slot)
    booking_listener = BookingListener(driver)
    try:
        # Click delete button
        delete_button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(@class, 'mat-raised-button')][.//span[normalize-space()='Delete']]"
            ))
        )
        driver.execute_script("arguments[0].click();", delete_button)

        # Click confirmation button
        confirm_button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(@class, 'mat-raised-button')][.//span[normalize-space()='Yes']]"
            ))
        )
        driver.execute_script("arguments[0].click();", confirm_button)

        # Check for error toasts
        try:
            status = booking_listener.confirm()
            return True, "Cancellation Confirmed"
        except ToastError as e:
            return False, e.toast_text
        except TimeoutException:
            return True, "Cancellation successful"
    except (NoSuchElementException, TimeoutException) as e:
        error_type = "not found" if isinstance(e, NoSuchElementException) else "timeout"
        print(f"Delete element {error_type}: {str(e)}")
        return False, f"Delete element {error_type}"
    except Exception as e:
        print(f"Error with delete element: {e}")
        return False, str(e)
    

