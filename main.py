#!/usr/bin/env python3
"""
Ad Watcher Bot - Automation script for logging into specific website
and sending screenshots via WhatsApp.
"""

import os
import time
import platform
import subprocess
import random
import argparse
import logging
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path
import pyautogui
import pytesseract
import numpy as np
import cv2
from PIL import Image
import io
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ad_watcher_bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Try importing macOS permission checks
try:
    from check_macos_permissions import (
        check_screenshot_permission,
        check_accessibility_permission,
        check_app_launching_permission,
        check_automation_permission
    )
    PERMISSION_UTILITY_AVAILABLE = True
except ImportError:
    logger.warning("check_macos_permissions.py not found - skipping advanced permission checks")
    PERMISSION_UTILITY_AVAILABLE = False
    check_screenshot_permission = check_accessibility_permission = \
        check_app_launching_permission = check_automation_permission = lambda: True

class AdWatcherBot:
    """Automation bot for task completion and WhatsApp reporting."""
    
    def __init__(self, complete_all_steps: bool = False, method: str = 'browser', skip_browser: bool = False):
        """Initialize the bot with environment variables and configurations."""
        load_dotenv()

        # Load URLs from environment
        self.WEBSITE_URL = os.getenv('WEBSITE_URL')
        self.LOGIN_URL = f"{self.WEBSITE_URL}/#/login"
        self.USER_PAGE_URL = f"{self.WEBSITE_URL}/#/user"
        self.WALLET_PAGE_URL = f"{self.WEBSITE_URL}/#/user/wallet"
        self.WITHDRAW_PAGE_URL = f"{self.WEBSITE_URL}/#/user/withdraw"
        
        # Load environment variables
        self.username = os.getenv('WEBSITE_USERNAME')
        self.password = os.getenv('WEBSITE_PASSWORD')
        self.fund_password = os.getenv('FUND_PASSWORD')
        self.default_identity = os.getenv('DEFAULT_IDENTITY', 'Internship')
        self.working_group = os.getenv('WORKING_GROUP')
        self.withdrawal_amount = os.getenv('WITHDRAWAL_AMOUNT')
        self.method = os.getenv('DEFAULT_METHOD', method).lower()
        self.user_agent = os.getenv('USER_AGENT', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        if not all([self.username, self.password, self.fund_password]):
            raise ValueError("Missing required environment variables: WEBSITE_USERNAME, WEBSITE_PASSWORD, FUND_PASSWORD")
        
        self.is_macos = platform.system().lower() == 'darwin'
        self.complete_all_steps = complete_all_steps
        self.driver = None
        self.task_url = None
        self.tasks_screenshot = None
        self.skip_browser = skip_browser
        
        if not skip_browser:
            self._check_permissions()
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.5
            self._setup_selenium()
        else:
            logger.info("Skipping browser setup for API-only mode")

    def _check_permissions(self):
        """Check macOS permissions if applicable."""
        if not self.is_macos:
            logger.info("Non-macOS system detected - skipping permission checks")
            self.accessibility_permission = self.screenshot_permission = \
                self.automation_permission = self.app_launching_permission = True
            return
        
        logger.info("Checking macOS permissions...")
        self.accessibility_permission = check_accessibility_permission()
        self.screenshot_permission = check_screenshot_permission()
        self.automation_permission = check_automation_permission()
        self.app_launching_permission = check_app_launching_permission()
        
        if not self.accessibility_permission:
            logger.error("CRITICAL: Accessibility permission required for mouse/keyboard control")
            logger.error("Please grant in System Preferences > Security & Privacy > Privacy > Accessibility")
            raise PermissionError("Accessibility permission not granted")
        
        if not self.screenshot_permission:
            logger.warning("Screen Recording permission not granted - manual WhatsApp verification required")
        if not self.automation_permission:
            logger.warning("Automation permission not granted - may see permission dialogs")
        if not self.app_launching_permission:
            logger.warning("App launching permission limited - may need to open WhatsApp manually")

    def _setup_selenium(self):
        """Set up Selenium WebDriver with Chrome options."""
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(f"--user-agent={self.user_agent}")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self._set_window_size()
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.warning(f"ChromeDriver initialization failed: {e}")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = webdriver.chrome.service.Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self._set_window_size()
                logger.info("Chrome WebDriver initialized using webdriver-manager")
            except Exception as e2:
                logger.error(f"Failed to initialize Chrome WebDriver: {e2}")
                raise

    def _set_window_size(self):
        """Set browser window size."""
        try:
            self.driver.maximize_window()
            current_size = self.driver.get_window_size()
            target_height = current_size.get('height', 1080)
            self.driver.set_window_size(735, target_height)
            logger.info(f"Browser window size set to 735x{target_height}")
        except Exception as e:
            logger.warning(f"Could not set window size: {e}")

    def login_to_website(self):
        """Log in to website using credentials from .env."""
        logger.info("Logging into website...")
        
        try:
            self.driver.get(self.LOGIN_URL)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)
            
            # Click button to reveal login form
            try:
                dialog_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".van-button"))
                )
                dialog_button.click()
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Could not find dialog button: {e}")
            
            # Find login fields
            username_field = self._find_field([
                "input[type='tel']",
                "input[placeholder='Ilagay ang Numero ng Telepono']",
                "input[placeholder*='Numero ng Telepono']",
                "input[name='username']",
                "input[name='phone']",
                ".van-field input",
                "#username"
            ])
            
            password_field = self._find_field([
                "input[placeholder='Ilagay ang Password sa Pag-login']",
                "input[type='password']",
                ".van-field__control",
                "#password"
            ])
            
            if not (username_field and password_field):
                self.driver.save_screenshot("login_fields_debug.png")
                raise NoSuchElementException("Login fields not found")
            
            # Enter credentials
            self._input_credentials(username_field, self.username)
            self._input_credentials(password_field, self.password)
            
            # Submit login form
            self._submit_login_form(password_field)
            
            # Verify login
            self._verify_login()
            logger.info("Login successful")
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            self.driver.save_screenshot("login_error.png")
            raise

    def _find_field(self, selectors: list) -> Optional[webdriver.remote.webelement.WebElement]:
        """Find the first visible field matching any of the provided selectors."""
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        logger.info(f"Found field with selector: {selector}")
                        return WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(element))
            except NoSuchElementException:
                continue
        return None

    def _input_credentials(self, field: webdriver.remote.webelement.WebElement, value: str):
        """Input credentials into a field, using fallback methods if necessary."""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", field)
            self.driver.execute_script("arguments[0].focus();", field)
            field.clear()
            field.send_keys(value)
            logger.info(f"Credentials entered for {value[:3]}...")
        except Exception as e:
            logger.warning(f"Standard input failed, using JavaScript: {e}")
            self.driver.execute_script("arguments[0].value = arguments[1];", field, value)
            logger.info("Credentials entered via JavaScript")

    def _submit_login_form(self, password_field: webdriver.remote.webelement.WebElement):
        """Submit the login form."""
        login_button_selectors = [
            "button:contains('Mag-log in Ngayon')",
            ".van-button--danger.van-button--large",
            "button[type='submit']",
            ".van-dialog__confirm",
            "#login-button"
        ]
        
        login_button = None
        for selector in login_button_selectors:
            try:
                if ":contains" in selector:
                    text = selector.split("'")[1]
                    login_button = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                else:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                if login_button.is_displayed():
                    break
            except NoSuchElementException:
                continue
        
        if login_button:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
            try:
                login_button.click()
                logger.info("Login button clicked")
            except Exception:
                self.driver.execute_script("arguments[0].click();", login_button)
                logger.info("Login button clicked via JavaScript")
        else:
            password_field.submit()
            logger.info("Form submitted via password field")

    def _verify_login(self):
        """Verify login success or handle errors."""
        time.sleep(3)
        toast_elements = self.driver.find_elements(By.CSS_SELECTOR, ".van-toast")
        for toast in toast_elements:
            if "display: none" not in (toast.get_attribute("style") or "") and toast.is_displayed():
                toast_text = toast.text.strip().lower()
                error_messages = [
                    "ilagay ang password", "ilagay ang numero", "mali ang password",
                    "mali ang numero", "hindi mahanap ang account", "nabigo ang pag-login",
                    "please enter password", "please enter phone number", "wrong password",
                    "wrong number", "account not found", "login failed", "invalid credentials"
                ]
                if any(error in toast_text for error in error_messages):
                    self.driver.save_screenshot("login_toast_error.png")
                    raise Exception(f"Login failed with error: {toast_text}")
        
        page_text = self.driver.page_source.lower()
        if any(error in page_text for error in ["error", "mali", "failed", "invalid"]):
            raise Exception("Login failed - error detected in page")
        
        if any(success in page_text for success in ["task hall", "home", "welcome", "matagumpay"]):
            logger.info("Login success confirmed")
        else:
            logger.warning("Login status unclear - proceeding with caution")

    def change_language_to_english(self):
        """Change website language to English."""
        logger.info("Changing language to English...")
        
        try:
            language_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Piliin ang Wika')]"))
            )
            language_button.click()
            WebDriverWait(self.driver, 10).until(EC.url_contains("#/language"))
            time.sleep(2)
            
            english_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'van-cell--clickable')]//span[text()='English']"))
            )
            english_option.click()
            time.sleep(3)
            
            WebDriverWait(self.driver, 5).until_not(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Piliin ang Wika')]"))
            )
            logger.info("Language changed to English")
        except Exception as e:
            logger.warning(f"Failed to change language: {e}")

    def check_account_identity(self) -> str:
        """Check account identity (e.g., Internship, VIP1)."""
        logger.info("Checking account identity...")
        
        try:
            self.driver.get(self.USER_PAGE_URL)
            time.sleep(3)
            identity_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div//p[text()='Your Identity']/following-sibling::p"))
            )
            identity_text = identity_element.text.strip()
            for option in ["Internship", "VIP1", "VIP2", "VIP3", "VIP4", "VIP5", "VIP6", "VIP7", "VIP8", "VIP9"]:
                if option in identity_text:
                    logger.info(f"Account identity: {option}")
                    return option
            logger.warning(f"Unknown identity: {identity_text}. Defaulting to {self.default_identity}")
            return self.default_identity
        except Exception as e:
            logger.error(f"Error checking identity: {e}")
            return self.default_identity

    def navigate_to_task_button(self, identity: str):
        """Navigate to the task button based on account identity."""
        logger.info(f"Navigating to {identity} task button...")
        
        try:
            self.driver.get(self.WEBSITE_URL)
            time.sleep(3)
            task_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//div[@class='TaskHall']//div[contains(@class, 'van-grid-item__content') and contains(text(), '{identity}')]"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", task_button)
            task_button.click()
            logger.info(f"{identity} task button clicked")
            
            self.task_url = self.driver.current_url
            while "taskList" not in self.task_url:
                self.task_url = self.driver.current_url
                time.sleep(1)
            logger.info(f"Task list URL: {self.task_url}")
        except Exception as e:
            logger.error(f"Error navigating to task button: {e}")
            raise

    def setup_task_prerequisites(self):
        """Set up prerequisites for task execution."""
        logger.info("Setting up task prerequisites...")
        self.change_language_to_english()
        user_identity = self.check_account_identity()
        self.navigate_to_task_button(user_identity)

    def start_tasks(self) -> bool:
        """Execute tasks until none remain or progress stalls."""
        logger.info("Starting task execution...")
        
        max_stalled_attempts = 3
        stalled_attempts = 0
        last_tasks_remaining = -1
        tasks_completed = 0
        
        while stalled_attempts < max_stalled_attempts:
            try:
                time.sleep(3)
                tasks_remaining = self._get_tasks_remaining()
                if tasks_remaining == 0:
                    logger.info("All tasks completed for today")
                    return tasks_completed > 0
                
                if last_tasks_remaining != -1 and tasks_remaining >= last_tasks_remaining:
                    stalled_attempts += 1
                    logger.warning(f"Task count did not decrease. Stalled attempt {stalled_attempts}/{max_stalled_attempts}")
                else:
                    stalled_attempts = 0
                last_tasks_remaining = tasks_remaining
                
                if stalled_attempts >= max_stalled_attempts:
                    logger.error("Task loop stalled. Aborting.")
                    break
                
                task_items = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".task-list .van-list .van-grid .van-grid-item"))
                )
                valid_tasks = [item for item in task_items if item.is_displayed() and item.find_elements(By.TAG_NAME, "img")]
                
                if not valid_tasks:
                    raise Exception("No valid tasks found")
                
                valid_tasks[0].click()
                time.sleep(3)
                
                new_url = self.driver.current_url
                if "/task/video/" in new_url:
                    self.handle_video_and_submit()
                    tasks_completed += 1
                elif "/myTask" in new_url:
                    self._handle_in_progress_task()
                    tasks_completed += 1
                else:
                    raise Exception(f"Unexpected URL: {new_url}")
                
            except Exception as e:
                logger.error(f"Task execution error: {e}")
                self.driver.save_screenshot("task_error.png")
                stalled_attempts += 1
                self.navigate_to_task_list()
        
        return tasks_completed > 0

    def _get_tasks_remaining(self) -> int:
        """Get the number of tasks remaining today."""
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='Tasks Remaining Today']/preceding-sibling::div//span"))
            )
            return int(element.text.strip())
        except Exception as e:
            logger.error(f"Error getting tasks remaining: {e}")
            self.driver.save_screenshot("tasks_remaining_error.png")
            raise

    def navigate_to_task_list(self):
        """Navigate to the task list page."""
        if "taskList" not in self.driver.current_url:
            logger.info("Navigating to task list...")
            self.driver.get(self.task_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".task-list .van-list .van-grid .van-grid-item"))
            )

    def handle_video_and_submit(self):
        """Handle video playback and submission."""
        logger.info("Handling video task...")
        self.start_video_playback()
        required_seconds = self.monitor_video_progress()
        self.submit_completed_task()

    def start_video_playback(self):
        """Start video playback."""
        logger.info("Starting video playback...")
        
        selectors = [
            ".video-js .vjs-big-play-button",
            ".video-js .vjs-play-control",
            "video",
            ".play-button"
        ]
        
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                element.click()
                logger.info(f"Video started with selector: {selector}")
                time.sleep(3)
                return
            except Exception:
                continue
        
        try:
            status = self.driver.find_element(By.XPATH, "//p[contains(text(), 'Currently watched')]")
            logger.info("Video already playing")
        except:
            logger.warning("Unable to start video playback")

    def monitor_video_progress(self) -> int:
        """Monitor video progress and return required watch time."""
        logger.info("Monitoring video progress...")
        
        required_seconds = 10
        try:
            requirement = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Watch') and contains(text(), 'seconds')]"))
            )
            import re
            numbers = re.findall(r'\d+', requirement.text)
            if numbers:
                required_seconds = int(numbers[0])
                logger.info(f"Required watch time: {required_seconds} seconds")
        except Exception as e:
            logger.warning(f"Could not determine watch time: {e}")
        
        max_wait = 600
        start_time = time.time()
        last_watched = 0
        
        while time.time() - start_time < max_wait:
            try:
                status = self.driver.find_elements(By.XPATH, "//p[contains(text(), 'Currently watched') and contains(text(), 'seconds')]")
                if status:
                    numbers = re.findall(r'Currently watched (\d+)', status[0].text)
                    if numbers:
                        watched_seconds = int(numbers[0])
                        if watched_seconds != last_watched:
                            logger.info(f"Progress: {watched_seconds}/{required_seconds} seconds")
                            last_watched = watched_seconds
                        if watched_seconds >= required_seconds:
                            return required_seconds
                time.sleep(1)
            except Exception:
                time.sleep(1)
        
        logger.warning("Video progress monitoring timed out")
        return required_seconds

    def submit_completed_task(self):
        """Submit the completed task."""
        logger.info("Submitting completed task...")
        
        selectors = [
            "button:contains('Submit Complete Task')",
            ".van-button--danger",
            "button:contains('Submit')",
            "#submit"
        ]
        
        submit_button = self._find_field(selectors)
        if not submit_button:
            self.driver.save_screenshot("submit_button_error.png")
            raise Exception("Submit button not found")
        
        self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
        try:
            submit_button.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", submit_button)
        
        try:
            WebDriverWait(self.driver, 15).until_not(EC.url_contains('/task/video/'))
            logger.info("Task submitted successfully")
        except TimeoutException:
            logger.warning("Timed out waiting for URL change after submission")

    def _handle_in_progress_task(self):
        """Handle an in-progress task."""
        try:
            pane = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".van-tabs__content .van-tab__pane:first-child"))
            )
            button = pane.find_element(By.CSS_SELECTOR, ".van-list .van-cell .TaskItem button")
            if "submit" in button.text.lower():
                button.click()
                time.sleep(3)
                if "/task/video/" in self.driver.current_url:
                    self.handle_video_and_submit()
                else:
                    raise Exception("Did not navigate to video page after clicking 'Submit'")
            else:
                raise Exception(f"Unexpected button text: {button.text}")
        except Exception as e:
            logger.error(f"Error handling in-progress task: {e}")
            raise

    def wait_and_screenshot(self):
        """Take screenshot of task list page and verify task completion."""
        logger.info("Taking task list screenshot...")
        
        self.navigate_to_task_list()
        time.sleep(5)
        
        try:
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return Array.from(document.images).every(img => img.complete && img.naturalWidth > 0);")
            )
            logger.info("All images loaded")
        except TimeoutException:
            logger.warning("Timeout waiting for images to load")
        
        tasks_completed = self._get_tasks_completed()
        screenshot_path = 'tasks_screenshot.png'
        self.driver.save_screenshot(screenshot_path)
        
        # Verify screenshot text
        screenshot = Image.open(screenshot_path).crop((720, 100, 1420, 325))
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        img = cv2.resize(img, None, fx=2, fy=2)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        cv2.imwrite("debug_tasks_screenshot.png", img)

        # Split image into two parts
        height, width = img.shape[:2]
        img1 = img[int(height*0.2):int(height*0.6), int(width*0.45):int(width*0.6)]
        img2 = img[int(height*0.6):height, 0:width]

        # Optimize img1 for single digit OCR
        h, w = img1.shape
        target_height = 32  # Optimal height for digit recognition
        if h != target_height:
            scale = target_height / h
            new_w = int(w * scale)
            img1 = cv2.resize(img1, (new_w, target_height), interpolation=cv2.INTER_CUBIC)

        # Add padding around the digit
        img1 = cv2.copyMakeBorder(img1, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=255)
        cv2.imwrite("debug_tasks_screenshot_part1.png", img1)
        cv2.imwrite("debug_tasks_screenshot_part2.png", img2)
        
        for psm in [7, 10, 6, 11]:
            # Config for part1: Digit whitelist + PSM for single digit/line
            config1 = f"--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789"
            text1 = pytesseract.image_to_string(img1, config=config1).strip().replace("\n", "")

            # If OEM 3 fails, try legacy engine for part1
            if not text1.isdigit():
                config1_legacy = f"--oem 1 --psm {psm} -c tessedit_char_whitelist=0123456789"
                text1 = pytesseract.image_to_string(img1, config=config1_legacy).strip().replace("\n", "")

            # Config for part2: Standard config (since it's working)
            config2 = f"--oem 3 --psm {psm}"
            text2 = pytesseract.image_to_string(img2, config=config2).strip().replace("\n", "")
            text = f"{text1} {text2}"
            logger.info(f"Tasks page screenshot text with PSM {psm}: {text}")
            if f'{tasks_completed} Tasks Completed Today' in text:
                logger.info(f"Screenshot verified with PSM {psm}")
                break
        else:
            raise Exception(f"Screenshot does not contain '{tasks_completed} Tasks Completed Today'")
        
        self.tasks_screenshot = screenshot_path
        logger.info(f"Screenshot saved: {screenshot_path}")

    def _get_tasks_completed(self) -> int:
        """Get the number of tasks completed today."""
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='Tasks Completed Today']/preceding-sibling::div//span"))
            )
            return int(element.text.strip())
        except Exception as e:
            logger.error(f"Error getting tasks completed: {e}")
            raise

    def is_whatsapp_visible(self) -> bool:
        """Check if WhatsApp is visible on screen."""
        logger.info("Checking WhatsApp visibility...")
        
        if self.is_macos and not self.screenshot_permission:
            logger.warning("No screenshot permission - assuming WhatsApp not visible")
            return False
        
        # Process-based detection for macOS
        if self.is_macos:
            try:
                result = subprocess.run(
                    ['osascript', '-e', 'tell application "System Events" to get name of (processes whose background only is false and name is "WhatsApp")'],
                    capture_output=True, text=True, timeout=3
                )
                if result.returncode == 0 and "whatsapp" in result.stdout.lower():
                    logger.info("WhatsApp detected via process list")
                    return True
            except Exception as e:
                logger.warning(f"Process detection failed: {e}")
        
        # Visual detection
        try:
            screenshot = pyautogui.screenshot()
            whatsapp_green = (37, 211, 102)
            tolerance = 30
            width, height = screenshot.size
            sample_points = [
                (width // 4, height // 10),
                (width // 10, height // 4),
                (width // 2, height // 10),
                (50, 50),
                (100, 100)
            ]
            
            green_pixels = sum(
                1 for x, y in sample_points
                if 0 <= x < width and 0 <= y < height
                and all(abs(screenshot.getpixel((x, y))[i] - whatsapp_green[i]) <= tolerance for i in range(3))
            )
            
            if green_pixels >= 2:
                logger.info("WhatsApp detected via color signature")
                return True
            
            text = pytesseract.image_to_string(screenshot, lang='eng').lower()
            if any(indicator in text for indicator in ['whatsapp', 'chats']):
                logger.info("WhatsApp detected via OCR")
                return True
        except Exception as e:
            logger.warning(f"Visual detection failed: {e}")
        
        logger.warning("WhatsApp not detected")
        return False

    def open_whatsapp(self):
        """Open WhatsApp and ensure it's visible."""
        logger.info("Opening WhatsApp...")
        
        os_name = platform.system().lower()
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            try:
                if os_name == 'darwin':
                    subprocess.run(['open', '-a', 'WhatsApp'], capture_output=True, text=True, timeout=10)
                    time.sleep(3)
                    if not self.is_whatsapp_visible():
                        subprocess.run(['open', 'https://web.whatsapp.com'], capture_output=True, text=True, timeout=10)
                        time.sleep(5)
                elif os_name == 'windows':
                    subprocess.run(['start', 'whatsapp://'], shell=True, capture_output=True, text=True, timeout=10)
                    time.sleep(3)
                    if not self.is_whatsapp_visible():
                        subprocess.run(['start', 'https://web.whatsapp.com'], shell=True, capture_output=True, text=True, timeout=10)
                        time.sleep(5)
                else:
                    subprocess.run(['xdg-open', 'https://web.whatsapp.com'], capture_output=True, text=True, timeout=10)
                    time.sleep(5)
                
                # Maximize window
                if os_name == 'darwin':
                    applescript = '''
                    tell application "WhatsApp" to activate
                    tell application "System Events"
                        try
                            tell process "WhatsApp"
                                set frontmost to true
                                repeat until frontmost is true
                                    delay 0.2
                                end repeat
                                delay 0.2
                                click menu item "Fill" of menu "Window" of menu bar 1
                                delay 1
                                click menu item "Zoom" of menu "Window" of menu bar 1
                            end tell
                        on error
                            log "Could not control WhatsApp"
                        end try
                    end tell
                    '''
                    subprocess.run(['osascript', '-e', applescript], capture_output=True)
                elif os_name == 'windows':
                    if pyautogui.getWindowsWithTitle('WhatsApp'):
                        pyautogui.getWindowsWithTitle('WhatsApp')[0].maximize()
                else:
                    pyautogui.hotkey('win', 'up')
                
                if self.is_whatsapp_visible():
                    logger.info("WhatsApp opened successfully")
                    return
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed: {e}")
            
            if attempt == max_attempts:
                logger.warning("MANUAL INTERVENTION REQUIRED: Please open WhatsApp manually")
                while not self.is_whatsapp_visible():
                    input("Press Enter after opening WhatsApp...")
                    retry = input("Type 'r' to retry, 'c' to continue, or 'q' to quit: ").lower()
                    if retry == 'c':
                        return
                    elif retry == 'q':
                        raise KeyboardInterrupt("User quit")

    def navigate_and_send_message(self):
        """Navigate WhatsApp and send screenshots."""
        logger.info("Navigating WhatsApp and sending message...")
        
        messages = [
            "Done with my tasks",
            "Finished my tasks today",
            "Tasks completed for today",
            "All tasks completed today",
            "Done tasking for today"
        ]
        
        current_time = datetime.now()
        if not (9, 30) <= (current_time.hour, current_time.minute) <= (20, 0):
            logger.info(f"Current time {current_time.strftime('%H:%M:%S')} is outside allowed hours (9:30 AM - 8:00 PM)")
            return
        
        try:
            pyautogui.click(105, 105)  # Search area
            time.sleep(1)
            pyautogui.hotkey('command', 'a')
            pyautogui.press('backspace')
            pyautogui.write(os.getenv('WORKING_GROUP'))
            time.sleep(1)
            pyautogui.click(205, 205)  # Select contact
            time.sleep(2)
            
            # Check for admin message and handle timing restrictions
            if self.check_for_admin_message():
                current_time = datetime.now()
                
                if current_time.hour < 9 or (current_time.hour == 9 and current_time.minute < 30):
                    time_until_930 = datetime.combine(current_time.date(), datetime.min.time().replace(hour=9, minute=30)) - current_time
                    if time_until_930.total_seconds() > 34200:  # More than 9.5 hours
                        logger.info("Time until 9:30 AM is greater than 9 hours and 30 minutes, unable to send message.")
                        return
                    
                    logger.info(f"Sleeping for {int(time_until_930.total_seconds())} seconds until 9:30 AM")
                    time.sleep(time_until_930.total_seconds())
                    
                    # Retry admin message check after waiting
                    for attempt in range(1, 11):
                        logger.info(f"Attempt {attempt} of 10 to check for admin message...")
                        if not self.check_for_admin_message():
                            logger.info("Admin message not found, sending message.")
                            break
                        logger.info("Admin message found, unable to send message.")
                        time.sleep(2)
                    else:
                        logger.info("Admin message still found after 10 attempts, unable to send message.")
                        return
                        
                elif current_time.hour >= 20:
                    logger.info("Current time is later than 8PM, unable to send message.")
                    return
                else:
                    logger.info("Current time is between 9:30 AM and 8PM, attempting to send message.")
                    time.sleep(20)  # Wait to ensure admin message is not found

            pyautogui.click(930, 930)  # Message input
            time.sleep(1)
            
            if self.tasks_screenshot and os.path.exists(self.tasks_screenshot):
                self.send_image_to_whatsapp(self.tasks_screenshot, random.choice(messages))
            logger.info("Message sent successfully")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    def check_for_admin_message(self) -> bool:
        """Check for admin-only message restriction."""
        if not self.screenshot_permission:
            logger.warning("No screenshot permission - skipping admin message check")
            return False
        
        try:
            screenshot = pyautogui.screenshot(region=(445, 905, 1024, 50))
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            img = cv2.resize(img, None, fx=2, fy=2)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            cv2.imwrite("debug_whatsapp_chatbox.png", img)
            
            text = pytesseract.image_to_string(img, lang='eng').strip()
            return any(msg in text for msg in ["Only admins can send messages", "Only admins"])
        except Exception as e:
            logger.warning(f"Admin message check failed: {e}")
            return False

    def check_balance_and_withdraw(self):
        """Check balance and withdraw if possible."""
        logger.info("Checking balance and withdrawal...")
        
        current_time = datetime.now()
        if current_time.weekday() > 4:
            logger.info(f"Today is {current_time.strftime('%A')} - no withdrawals on weekends")
            return
        if (current_time.hour, current_time.minute) < (9, 0):
            time_until_9am = (datetime.strptime("09:00:00", "%H:%M:%S") - 
                            datetime.strptime(current_time.strftime("%H:%M:%S"), "%H:%M:%S")).total_seconds()
            logger.info(f"Waiting {time_until_9am} seconds until 9:00 AM")
            time.sleep(time_until_9am)
        
        try:
            self.driver.get(self.USER_PAGE_URL)
            time.sleep(3)
            balance = float(WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div//p[text()='Personal Balance(PHP)']/following-sibling::p"))
            ).text.strip())
            logger.info(f"Balance: {balance} PHP")
            
            if balance < float(self.withdrawal_amount):
                logger.info("Balance insufficient for withdrawal")
                return
            
            self.driver.get(self.WALLET_PAGE_URL)
            time.sleep(3)
            withdrawal_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'van-tab')]//span[text()='Withdrawal Records']"))
            )
            withdrawal_tab.click()
            time.sleep(3)
            
            today = current_time.strftime('%d-%m-%Y')
            if self._has_withdrawal_today(today):
                logger.info("Withdrawal already made today")
                return
            
            self._perform_withdrawal()
            self._verify_withdrawal(today)
        except Exception as e:
            logger.error(f"Withdrawal process failed: {e}")
            self.driver.save_screenshot("withdrawal_error.png")

    def _has_withdrawal_today(self, today: str) -> bool:
        """Check if a withdrawal was made today."""
        try:
            items = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'FundItem') and contains(@class, 'van-cell')]")
            for item in items:
                date_text = item.find_element(By.XPATH, ".//span[contains(text(), '-')]").text.strip()
                if today in date_text:
                    amount = item.find_element(By.XPATH, ".//span[contains(@class, 'money-withdraw')]").text.strip()
                    status = item.find_element(By.XPATH, ".//span[contains(@style, 'color: gray')]").text.strip()
                    logger.info(f"Today's withdrawal: Date={date_text}, Amount={amount}, Status={status}")
                    return True
            return False
        except Exception as e:
            logger.warning(f"Error checking withdrawal records: {e}")
            return False

    def _perform_withdrawal(self):
        """Perform the withdrawal process."""
        self.driver.get(self.WITHDRAW_PAGE_URL)
        time.sleep(3)
        amount_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class, 'van-grid-item__content') and normalize-space(text()) = '{self.withdrawal_amount}']"))
        )
        amount_button.click()
        logger.info(f"Selected {self.withdrawal_amount} PHP withdrawal")
        
        password_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Please enter the fund password']")
        password_input.send_keys(self.fund_password)
        logger.info("Entered fund password")
        
        submit_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'van-button--danger') and .//span[text()='Submit']]")
        submit_button.click()
        logger.info("Withdrawal submitted")
        time.sleep(3)

    def _verify_withdrawal(self, today: str):
        """Verify the withdrawal was successful."""
        self.driver.get(self.WALLET_PAGE_URL)
        time.sleep(3)
        withdrawal_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'van-tab')]//span[text()='Withdrawal Records']"))
        )
        withdrawal_tab.click()
        time.sleep(3)
        
        items = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'FundItem') and contains(@class, 'van-cell')]")
        for item in items:
            date_text = item.find_element(By.XPATH, ".//span[contains(text(), '-')]").text.strip()
            if today in date_text:
                status = item.find_element(By.XPATH, ".//span[contains(@style, 'color: gray')]").text.strip()
                logger.info(f"Withdrawal verified: Status={status}")
                return
        logger.warning("No withdrawal found after submission")
        self.driver.save_screenshot("withdrawal_verification_error.png")

    def send_image_to_whatsapp(self, image_path: str, caption: str) -> bool:
        """Send an image to WhatsApp with a caption."""
        os_name = platform.system().lower()
        abs_path = os.path.abspath(image_path)
        
        if os_name == 'darwin':
            try:
                # close Preview first
                script = f'''
                tell application "Preview" to quit
                delay 0.5
                tell application "WhatsApp" to activate
                delay 1
                tell application "System Events"
                    tell process "WhatsApp"
                        do shell script "open '{abs_path}'"
                        delay 1
                        tell application "System Events" to keystroke "a" using command down
                        delay 0.5
                        tell application "System Events" to keystroke "c" using command down
                        delay 0.5
                        tell application "WhatsApp" to activate
                        delay 0.5
                        click at {{930, 930}}
                        delay 0.5
                        tell application "System Events" to keystroke "v" using command down
                        delay 2
                    end tell
                end tell
                '''
                subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=30)
                pyautogui.hotkey('command', 'a')
                pyautogui.press('backspace')
                pyautogui.write(caption)
                pyautogui.press('enter')
                logger.info("Image sent via macOS AppleScript")
                return True
            except Exception as e:
                logger.warning(f"macOS image sending failed: {e}")
                return False
        elif os_name == 'windows':
            # Note that this method has not been tested yet
            try:
                from win32clipboard import OpenClipboard, EmptyClipboard, SetClipboardData, CloseClipboard, CF_DIB
                img = Image.open(image_path)
                output = io.BytesIO()
                img.convert("RGB").save(output, format='BMP')
                data = output.getvalue()[14:]
                output.close()
                
                OpenClipboard()
                EmptyClipboard()
                SetClipboardData(CF_DIB, data)
                CloseClipboard()
                
                pyautogui.click(930, 930)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(2)
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('backspace')
                pyautogui.write(caption)
                pyautogui.press('enter')
                logger.info("Image sent via Windows clipboard")
                return True
            except Exception as e:
                logger.warning(f"Windows image sending failed: {e}")
                return False
        else:
            # Note that this method has not been tested yet
            try:
                pyautogui.click(900, 930)
                time.sleep(1)
                pyautogui.click(950, 850)
                time.sleep(2)
                pyautogui.write(abs_path)
                pyautogui.press('enter')
                time.sleep(2)
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('backspace')
                pyautogui.write(caption)
                pyautogui.press('enter')
                logger.info("Image sent via generic method")
                return True
            except Exception as e:
                logger.warning(f"Generic image sending failed: {e}")
                return False

    def close_whatsapp(self):
        """Close WhatsApp application."""
        logger.info("Closing WhatsApp...")
        try:
            if platform.system().lower() == 'darwin':
                pyautogui.hotkey('cmd', 'q')
            else:
                pyautogui.hotkey('alt', 'f4')
            logger.info("WhatsApp closed")
        except Exception as e:
            logger.warning(f"Error closing WhatsApp: {e}")

    def complete_tasks_via_api(self) -> bool:
        """Complete tasks using API method."""
        logger.info("Completing tasks via API...")
        
        session = requests.Session()
        headers = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': self.WEBSITE_URL,
            'referer': f'{self.WEBSITE_URL}/',
            'user-agent': self.user_agent,
        }
        
        login_data = {
            'username': self.username,
            'password': self.password,
            'language': 'fil_ph',
            'referer': self.LOGIN_URL,
        }
        
        try:
            login_resp = session.post('https://api.aksystemph.com/api/User/login', headers=headers, data=login_data)
            login_resp.raise_for_status()
            login_json = login_resp.json()
            if login_json.get('code') != 1:
                raise Exception(f"API login error: {login_json}")
            
            token = login_json['data']['token']
            task_num = login_json['data']['task_num']
            level = login_json['data']['level']
            logger.info(f"API login successful. Identity: {login_json['data']['useridentity']}, Level: {level}")
            
            while True:
                task_list_data = {
                    'id': str(task_num),
                    'task_level': str(level),
                    'page_no': '1',
                    'language': 'fil_ph',
                    'referer': f'{self.WEBSITE_URL}/#/taskList/{task_num}/{level}',
                    'token': token,
                }
                task_list_resp = session.post('https://api.aksystemph.com/api/Task/getTaskList', headers=headers, data=task_list_data)
                task_list_resp.raise_for_status()
                task_list_json = task_list_resp.json()
                
                if task_list_json.get('code') != 1:
                    logger.error(f"Task list API error: {task_list_json}")
                    return False
                
                tasks_remaining = task_list_json['data']['taskNumArr'][0] if task_list_json['data']['taskNumArr'] else 0
                logger.info(f"Tasks remaining: {tasks_remaining}")
                
                if not task_list_json['data']['list'] or tasks_remaining == 0:
                    logger.info("No tasks available via API")
                    break
                
                task_id = task_list_json['data']['list'][0]['id']
                receive_data = {
                    'id': str(task_id),
                    'language': 'fil_ph',
                    'referer': f'{self.WEBSITE_URL}/#/taskList/{task_num}/{level}',
                    'token': token,
                }
                receive_resp = session.post('https://api.aksystemph.com/api/Task/receiveTask', headers=headers, data=receive_data)
                if receive_resp.status_code != 200 or receive_resp.json().get('code') != 1:
                    logger.warning(f"Failed to receive task {task_id}: {receive_resp.text}")
                    continue
                
                submit_data = {
                    'id': str(task_id),
                    'seconds': '11',
                    'language': 'fil_ph',
                    'referer': f'{self.WEBSITE_URL}/#/task/video/{task_id}',
                    'token': token,
                }
                submit_resp = session.post('https://api.aksystemph.com/api/Task/submitTask', headers=headers, data=submit_data)
                if submit_resp.status_code == 200 and submit_resp.json().get('code') == 1:
                    logger.info(f"Task {task_id} submitted successfully")
                    time.sleep(10)
                else:
                    logger.warning(f"Failed to submit task {task_id}: {submit_resp.text}")
            
            return True
        except Exception as e:
            logger.error(f"API task completion failed: {e}")
            return False

    def run(self, skip_whatsapp: bool = False):
        """Execute the full automation workflow."""
        logger.info("Starting Ad Watcher Bot...")
        try:
            self.login_to_website()
            self.setup_task_prerequisites()
            tasks_completed = self.complete_tasks_via_api() if self.method == 'api' else self.start_tasks()
            if tasks_completed or self.complete_all_steps:
                self.check_balance_and_withdraw()
                self.wait_and_screenshot()
                if not skip_whatsapp:
                    self.open_whatsapp()
                    self.navigate_and_send_message()
                    self.close_whatsapp()
            logger.info("Bot completed successfully")
        except Exception as e:
            logger.error(f"Bot execution failed: {e}")
            raise
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up...")
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
        elif self.skip_browser:
            logger.info("No browser to clean up in API-only mode")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Ad Watcher Bot")
    parser.add_argument('-c', '--complete', action='store_true', help='Complete all steps even if no tasks were done')
    parser.add_argument('--api', action='store_true', help='Use API method for task completion')
    parser.add_argument('-sw', '--skip-whatsapp', action='store_true', help='Skip WhatsApp message sending')
    args = parser.parse_args()
    
    bot = None
    try:
        skip_browser = args.api and args.skip_whatsapp
        bot = AdWatcherBot(complete_all_steps=args.complete, method='api' if args.api else 'browser', skip_browser=skip_browser)
        if args.api:
            success = bot.complete_tasks_via_api()
            logger.info("API tasks completed successfully" if success else "API task completion failed")
        else:
            bot.run(skip_whatsapp=args.skip_whatsapp)
        return 0
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        if bot and not (args.api and args.skip_whatsapp):
            bot.cleanup()

if __name__ == "__main__":
    exit(main())