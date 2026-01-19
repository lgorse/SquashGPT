import os
import time

from dotenv import load_dotenv
import perf_logger

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def login_to_clublocker(driver):
    start_time = perf_logger.log_perf_start("login_to_clublocker")
    # Get credentials securely
    timeout = 10
    load_dotenv()
    username = os.getenv("username")
    password = os.getenv("password")

    try:
        # Navigate to the website
        print("Navigating to clublocker.com...")
        nav_start = perf_logger.log_perf_start("login:navigate_to_site")
        driver.get("https://clublocker.com/")
        perf_logger.log_perf_end("login:navigate_to_site", nav_start)

        username_field = None
        password_field = None
        try:
            username_selector = "//input[@name='username']"
            username_field = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, username_selector))
            )
        except Exception as error:
            print(f"Error type: {type(error).__name__} on username")
            return error

        try:
            password_selector = "//input[@name='password']"
            password_field = driver.find_element(By.XPATH, password_selector)

           ## password_field = WebDriverWait(driver, timeout).until(
           ##     EC.presence_of_element_located((By.XPATH, password_selector))
           ## )
        except Exception as error:
            print(f"Error type: {type(error).__name__} on password")
            return error

        if username_field and password_field:
            print("Found login fields, entering credentials...")

            # Clear fields and enter credentials
            username_field.clear()
            username_field.send_keys(username)

            password_field.clear()
            password_field.send_keys(password)

            login_element = None
            try:
                login_selector = "//button[@type='submit']"
                login_element = driver.find_element (By.XPATH, login_selector)
                # login_element = WebDriverWait(driver, timeout).until(
                #     EC.presence_of_element_located((By.XPATH, login_selector))
                # )
            except Exception as error:
                print(f"Error type: {type(error).__name__} on submit CTA")
                return error

            if login_element:
                print("Found login element, clicking...")
                login_click_start = perf_logger.log_perf_start("login:submit_and_wait")
                login_element.click()
                # Check if login was successful (you may need to customize this)
                current_url = driver.current_url
                WebDriverWait(driver, timeout).until(EC.url_changes(current_url))
                perf_logger.log_perf_end("login:submit_and_wait", login_click_start)
                print(f"Current URL after login attempt: {current_url}")
                perf_logger.log_perf_end("login_to_clublocker", start_time)
            else:
                print("Could not find submit button")
                perf_logger.log_perf_end("login_to_clublocker", start_time)

        else:
            print("Could not find username and/or password fields")
            print(
                "You may need to manually inspect the website and update the selectors"
            )
            perf_logger.log_perf_end("login_to_clublocker", start_time)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        perf_logger.log_perf_end("login_to_clublocker", start_time)
        return e
