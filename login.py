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


def login_to_clublocker(sb):
    start_time = perf_logger.log_perf_start("login_to_clublocker")
    timeout = 10
    load_dotenv()
    username = os.getenv("username")
    password = os.getenv("password")

    try:
        # Navigate using UC mode with reconnect for stealth
        print("Navigating to clublocker.com with UC reconnect...")
        nav_start = perf_logger.log_perf_start("login:navigate_to_site")
        sb.uc_open_with_reconnect("https://clublocker.com/", reconnect_time=4)
        perf_logger.log_perf_end("login:navigate_to_site", nav_start)

        # Find and fill login fields
        print("Finding login fields...")
        username_field = WebDriverWait(sb.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='username']"))
        )
        password_field = sb.driver.find_element(By.XPATH, "//input[@name='password']")

        print("Entering credentials...")
        username_field.clear()
        username_field.send_keys(username)
        password_field.clear()
        password_field.send_keys(password)

        # Click login button
        print("Clicking login button...")
        login_click_start = perf_logger.log_perf_start("login:submit_and_wait")
        current_url = sb.driver.current_url
        login_button = sb.driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()

        # Cloudflare challenge appears AFTER login click
        print("Checking for Cloudflare challenge after login...")
        time.sleep(3)

        captcha_frames = sb.driver.find_elements(By.CSS_SELECTOR, "iframe")
        if captcha_frames:
            print(f"Cloudflare challenge detected ({len(captcha_frames)} iframes), attempting bypass...")
            try:
                sb.uc_gui_click_cf()
                time.sleep(3)
                print("Challenge bypass attempted")
            except Exception as e:
                print(f"Challenge bypass error: {type(e).__name__}")
        else:
            print("No Cloudflare challenge detected")

        # Wait for URL to change (successful login redirects away from login page)
        print("Waiting for redirect...")
        WebDriverWait(sb.driver, 20).until(EC.url_changes(current_url))
        perf_logger.log_perf_end("login:submit_and_wait", login_click_start)

        print(f"Login successful. Current URL: {sb.driver.current_url}")
        perf_logger.log_perf_end("login_to_clublocker", start_time)

    except Exception as e:
        print(f"Login failed: {type(e).__name__}: {str(e)}")
        perf_logger.log_perf_end("login_to_clublocker", start_time)
        raise e  # Raise exception instead of returning it
