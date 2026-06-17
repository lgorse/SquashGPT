import threading
import time
import atexit
from datetime import datetime, timedelta
from selenium.common.exceptions import WebDriverException
import squash
import login
import perf_logger


class SessionManager:
    """Singleton class to manage persistent WebDriver session"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SessionManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.driver = None
        self.last_activity = None
        self.session_timeout = 1800  # 30 minutes in seconds
        self.request_lock = threading.Lock()
        self.is_logged_in = False
        self.request_count = 0
        self.max_requests_before_reset = 100  # Reset driver after 100 requests to prevent memory leaks
        self._initialized = True

        # Register cleanup on exit
        atexit.register(self.cleanup)

    @classmethod
    def get_instance(cls):
        """Get the singleton instance"""
        return cls()

    def get_driver(self, mode=None):
        """
        Get active driver or create new one if needed.
        Thread-safe via locking.
        """
        with self.request_lock:
            perf_logger.log_perf("session_manager", "Acquiring driver")

            # Check if driver needs reset
            if self._should_reset_session():
                perf_logger.log_perf("session_manager", "Resetting session (timeout or max requests)")
                self._reset_session(mode)

            # Check if driver exists and is healthy
            if self.driver is None or not self._is_driver_healthy():
                perf_logger.log_perf("session_manager", "Creating new driver session")
                self._reset_session(mode)
            else:
                perf_logger.log_perf("session_manager", f"Reusing existing session (request #{self.request_count})")

            self.last_activity = datetime.now()
            self.request_count += 1
            return self.driver

    def ensure_logged_in(self):
        """
        Ensure user is logged in. Re-login if session expired.
        Must be called with request_lock held (via get_driver context).
        """
        if not self.is_logged_in or self._is_session_expired():
            perf_logger.log_perf("session_manager", "Session expired, re-authenticating")
            start_time = perf_logger.log_perf_start("session:re-login")
            try:
                login.login_to_clublocker(self.driver)
                self.is_logged_in = True
                perf_logger.log_perf_end("session:re-login", start_time)
            except Exception as e:
                perf_logger.log_perf_end("session:re-login", start_time)
                self.is_logged_in = False
                raise e  # Propagate login failure
        else:
            perf_logger.log_perf("session_manager", "Session active, skipping login")

    def _should_reset_session(self):
        """Check if session should be reset due to timeout or request count"""
        # Check request count threshold
        if self.request_count >= self.max_requests_before_reset:
            return True

        # Check timeout
        if self.last_activity:
            elapsed = (datetime.now() - self.last_activity).total_seconds()
            if elapsed > self.session_timeout:
                return True

        return False

    def _is_session_expired(self):
        """Check if login session has expired by checking current URL"""
        try:
            if self.driver is None:
                return True

            # self.driver is SB instance, need underlying driver
            driver = self.driver.driver if hasattr(self.driver, 'driver') else self.driver
            current_url = driver.current_url.lower()
            # If we're on the login page, session expired
            if "login" in current_url and "reservations" not in current_url:
                return True

            return False
        except WebDriverException:
            return True

    def _is_driver_healthy(self):
        """Check if driver is responsive"""
        try:
            if self.driver is None:
                return False

            # self.driver is SB instance, need underlying driver
            driver = self.driver.driver if hasattr(self.driver, 'driver') else self.driver
            # Try to get current URL as health check
            _ = driver.current_url
            return True
        except WebDriverException as e:
            perf_logger.log_perf("session_manager", f"Driver unhealthy: {str(e)}")
            return False

    def _reset_session(self, mode=None):
        """Force creation of new driver and login session"""
        # Cleanup old driver (SB context)
        if self.driver is not None:
            try:
                # Use stored context manager for proper cleanup
                if hasattr(self.driver, '_sb_context'):
                    self.driver._sb_context.__exit__(None, None, None)
                elif hasattr(self.driver, '__exit__'):
                    self.driver.__exit__(None, None, None)
                else:
                    self.driver.quit()
            except Exception as e:
                perf_logger.log_perf("session_manager", f"Error quitting old driver: {str(e)}")

        # Create new driver and login
        start_time = perf_logger.log_perf_start("session:full_reset")
        self.driver = squash.setup_driver(mode)
        try:
            login.login_to_clublocker(self.driver)
            self.is_logged_in = True
        except Exception as e:
            self.is_logged_in = False
            perf_logger.log_perf_end("session:full_reset", start_time)
            raise e  # Propagate login failure
        self.request_count = 0
        perf_logger.log_perf_end("session:full_reset", start_time)

    def reset(self):
        """Public method to force session reset"""
        with self.request_lock:
            perf_logger.log_perf("session_manager", "Manual session reset requested")
            self._reset_session()

    def cleanup(self):
        """Cleanup driver on shutdown"""
        if self.driver is not None:
            try:
                perf_logger.log_perf("session_manager", "Cleaning up driver on shutdown")
                # Use stored context manager for proper cleanup
                if hasattr(self.driver, '_sb_context'):
                    self.driver._sb_context.__exit__(None, None, None)
                elif hasattr(self.driver, '__exit__'):
                    self.driver.__exit__(None, None, None)
                else:
                    self.driver.quit()
                self.driver = None
            except Exception as e:
                print(f"Error during cleanup: {str(e)}")
