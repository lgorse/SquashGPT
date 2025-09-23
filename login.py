import os
import time

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def login_to_clublocker(driver):
    # Get credentials securely
    timeout = 10
    load_dotenv()
    username = os.getenv("username")
    password = os.getenv("password")

    try:
        # Navigate to the website
        print("Navigating to clublocker.com...")
        driver.get("https://clublocker.com/")

        # Wait for page to load
        # time.sleep(2)

        # Try to find username/email field
        username_selectors = [
            "//input[@type='email']",
            "//input[@name='username']",
            "//input[@name='email']",
            "//input[@id='username']",
            "//input[@id='email']",
            "#username",
            "#email",
        ]

        username_field = None
        password_field = None
        try:
            username_selector = "//input[@name='username']"
            username_field = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, username_selector))
            )
        except Exception as error:
            print(f"Error type: {type(error).__name__}")

        try:
            password_selector = "//input[@name='password']"
            password_field = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, password_selector))
            )
        except Exception as error:
            print(f"Error type: {type(error).__name__}")

        """for selector in username_selectors:
            try:
                if selector.startswith("//"):
                    username_field = WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    ##driver.find_element(By.XPATH, selector)
                elif selector.startswith("#"):
                    username_field = WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.Id, selector[1:]))
                    )
                    # username_field = driver.find_element(By.ID, selector[1:])
                else:
                    username_field = WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                # username_field = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue"""

        # Try to find password field
        """password_field = None
        password_selectors = [
            "//input[@type='password']",
            "//input[@name='password']",
            "#password",
        ]

        for selector in password_selectors:
            try:
                if selector.startswith("//"):
                    password_field = WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    # password_field = driver.find_element(By.XPATH, selector)
                elif selector.startswith("#"):
                    password_field = WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.Id, selector[1:]))
                    )
                    # driver.find_element(By.ID, selector[1:])
                else:
                    password_field = WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    # driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue"""

        if username_field and password_field:
            print("Found login fields, entering credentials...")

            # Clear fields and enter credentials
            username_field.clear()
            username_field.send_keys(username)

            password_field.clear()
            password_field.send_keys(password)

            # You'll need to inspect the actual login form to get the correct selectors
            # These are placeholder selectors - update them based on the actual website

            # Look for login button/link (common selectors to try)
            login_selectors = [
                "//a[contains(text(), 'Login')]",
                "//a[contains(text(), 'Sign In')]",
                "//button[contains(text(), 'Login')]",
                "//input[@type='submit' and @value='Login']",
                "#login-button",
                ".btn btn-primary login-btn",
            ]

            login_element = None
            try:
                login_selector = "//button[@type='submit']"
                login_element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, login_selector))
                )
            except Exception as error:
                print(f"Error type: {type(error).__name__}")

            """for selector in login_selectors:
                try:
                    if selector.startswith("//"):
                        login_element = WebDriverWait(driver, timeout).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        # driver.find_element(By.XPATH, selector)
                    elif selector.startswith("#"):
                        login_element = WebDriverWait(driver, timeout).until(
                            EC.presence_of_element_located((By.Id, selector[1:]))
                        )
                        # driver.find_element(By.ID, selector[1:])
                    elif selector.startswith("."):
                        login_element = WebDriverWait(driver, timeout).until(
                            EC.presence_of_element_located(
                                (By.CLASS_NAME, selector[1:])
                            )
                        )
                        # driver.find_element(By.CLASS_NAME, selector[1:])
                    else:
                        login_element = WebDriverWait(driver, timeout).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        # driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue"""

            if login_element:
                print("Found login element, clicking...")
                login_element.click()

                # Check if login was successful (you may need to customize this)
                current_url = driver.current_url
                WebDriverWait(driver, timeout).until(EC.url_changes(current_url))
                print(f"Current URL after login attempt: {current_url}")

                # Keep browser open for a bit to see results
                print(
                    "Login attempt completed. Browser will remain open for 10 seconds..."
                )
                # time.sleep(5)

            else:
                print("Could not find submit button")
        else:
            print("Could not find username and/or password fields")
            print(
                "You may need to manually inspect the website and update the selectors"
            )

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        """driver.quit()"""
