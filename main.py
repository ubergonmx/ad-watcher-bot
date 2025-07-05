#!/usr/bin/env python3
"""
Ad Watcher Bot - Automation script for logging into akqaflicksph.com 
and sending screenshots via WhatsApp.
"""

import os
import time
import pyautogui
import io
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
from PIL import Image
import logging
import platform
import subprocess
import random
import argparse
import numpy as np
import cv2
import requests

# Configure logging first
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import permission checking functions from the dedicated utility
try:
    from check_macos_permissions import check_screenshot_permission, check_accessibility_permission, check_app_launching_permission, check_automation_permission, test_selenium_screenshot
except ImportError:
    # Fallback if check_macos_permissions.py is not available
    logger.warning("check_macos_permissions.py not found - using basic permission checks")
    check_screenshot_permission = None
    check_accessibility_permission = None 
    check_app_launching_permission = None
    check_automation_permission = None
    test_selenium_screenshot = None

class AdWatcherBot:
    def __init__(self, complete_all_steps=False):
        """Initialize the automation bot."""
        load_dotenv()
        
        self.username = os.getenv('WEBSITE_USERNAME')
        self.password = os.getenv('WEBSITE_PASSWORD')
        self.fund_password = os.getenv('FUND_PASSWORD')
        self.default_identity = os.getenv('DEFAULT_IDENTITY')
        self.website_url = os.getenv('WEBSITE_URL')
        self.default_method = os.getenv('DEFAULT_METHOD', 'browser').lower()
        
        if not self.username or not self.password or not self.fund_password:
            raise ValueError("Please set WEBSITE_USERNAME, WEBSITE_PASSWORD, and FUND_PASSWORD in your .env file")
        
        # Initialize permission flags
        self.is_macos = platform.system().lower() == 'darwin'
        self.permissions_utility_available = all([
            check_accessibility_permission, 
            check_screenshot_permission, 
            check_app_launching_permission, 
            check_automation_permission
        ])
        
        self.accessibility_permission_granted = not self.is_macos
        self.screenshot_permission_granted = not self.is_macos
        self.automation_permission_granted = not self.is_macos
        self.app_launching_permission_granted = not self.is_macos
        
        # Check macOS permissions before proceeding
        if self.is_macos:
            self.check_macos_permissions()
        else:
            logger.info("Not running on macOS - skipping permission checks, assuming granted.")
        
        self.driver = None
        self.setup_selenium()
        
        # Configure PyAutoGUI for safety
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        
        self.complete_all_steps = complete_all_steps
    
    def check_macos_permissions(self):
        """Check macOS permissions using the dedicated permission checker utility."""
        if platform.system().lower() != 'darwin':
            logger.info("Not running on macOS - skipping permission checks")
            return
        
        logger.info("Checking macOS permissions...")
        
        # Use imported functions if available, otherwise skip detailed checks
        if not self.permissions_utility_available:
            logger.warning("Permission checking utility not available - using basic checks")
            logger.warning("Run 'python check_macos_permissions.py' separately to verify permissions")
            # Flags will retain their initial values (False for macOS if utility missing)
            return
        
        # Check Accessibility permission (CRITICAL - required for mouse/keyboard control)
        self.accessibility_permission_granted = check_accessibility_permission()
        
        # Check Screen Recording permission (OPTIONAL - only needed for WhatsApp detection)
        self.screenshot_permission_granted = check_screenshot_permission()
        
        # Check Automation permission (HELPFUL - prevents permission dialogs)
        self.automation_permission_granted = check_automation_permission()
        
        # Check App Launching permission (OPTIONAL - helpful for WhatsApp opening)
        self.app_launching_permission_granted = check_app_launching_permission()
        
        # Only stop execution if CRITICAL permissions are missing
        if not self.accessibility_permission_granted:
            logger.error("❌ CRITICAL macOS permission is missing!")
            logger.error("The bot cannot function without this permission.")
            logger.error("")
            
            logger.error("🖱️  MISSING: Accessibility permission") 
            logger.error("   This is required for mouse clicks and keyboard input")
            logger.error("   THE BOT WILL NOT WORK WITHOUT THIS")
            
            logger.error("")
            logger.error("🔧 How to grant Accessibility permission:")
            logger.error("1. Open System Preferences/Settings")
            logger.error("2. Go to Security & Privacy > Privacy")
            logger.error("3. Click 'Accessibility' in the left sidebar")
            logger.error("4. Check the box next to 'Terminal' or 'Cursor' (depending on where you ran the script)")
            logger.error("5. You may need to restart the application")
            logger.error("")
            logger.error("🔄 After granting permission, restart this script")
            logger.error("💡 Note: You might see permission dialogs when running the script for the first time")
            logger.error("")
            logger.error("💡 TIP: Run 'python check_macos_permissions.py' for detailed permission testing")
            
            raise PermissionError("Required macOS Accessibility permission not granted. Please grant permission and try again.")
        
        # Warn about optional permissions but don't stop execution
        if not self.screenshot_permission_granted:
            logger.warning("⚠️  Screen Recording permission not granted")
            logger.warning("   This is only needed for automatic WhatsApp detection")
            logger.warning("   The bot will ask you to manually verify WhatsApp is open")
            logger.warning("   Main bot functionality (screenshots, tasks) will work fine")
        
        if not self.automation_permission_granted:
            logger.warning("⚠️  Automation permission not granted")
            logger.warning("   You may see permission dialogs when the bot tries to open WhatsApp")
            logger.warning("   To prevent this, grant Automation permission in System Preferences:")
            logger.warning("   Security & Privacy > Privacy > Automation > Terminal/Cursor > System Events")
        
        if not self.app_launching_permission_granted:
            logger.warning("⚠️  App launching permissions are limited")
            logger.warning("   The bot will use manual fallback for opening WhatsApp")
            logger.warning("   You may need to open WhatsApp manually when prompted")
        
        # Summary
        if self.accessibility_permission_granted and self.screenshot_permission_granted and self.automation_permission_granted and self.app_launching_permission_granted:
            logger.info("✅ All macOS permissions granted - bot will work perfectly!")
        elif self.accessibility_permission_granted:
            logger.info("✅ Core macOS permissions granted - bot will work with minor limitations")
            if not self.automation_permission_granted:
                logger.info("   You may see permission dialogs during WhatsApp opening")
            if not self.screenshot_permission_granted:
                logger.info("   You may need to manually verify WhatsApp is open")
        
        logger.info("Continuing with bot execution...")
    
    def setup_selenium(self):
        """Set up Selenium WebDriver with Chrome options."""
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Try to use ChromeDriver directly first
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set window size
            try:
                self.driver.maximize_window() 
                current_size = self.driver.get_window_size()
                target_height = current_size.get('height', 1080) 
                self.driver.set_window_size(735, target_height)
                logger.info(f"Browser window size set to 735x{target_height}")
            except Exception as e_size:
                logger.warning(f"Could not set custom window size: {e_size}. Using default size.")

            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.warning(f"ChromeDriver not found in PATH: {e}")
            logger.info("Trying to use webdriver-manager to auto-download ChromeDriver...")
            
            try:
                # Use webdriver-manager to automatically download and setup ChromeDriver
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                # Set window size
                try:
                    self.driver.maximize_window()
                    current_size = self.driver.get_window_size()
                    target_height = current_size.get('height', 1080)
                    self.driver.set_window_size(950, target_height)
                    logger.info(f"Browser window size set to 950x{target_height}")
                except Exception as e_size:
                    logger.warning(f"Could not set custom window size: {e_size}. Using default size.")
                
                logger.info("Chrome WebDriver initialized successfully using webdriver-manager")
            except ImportError:
                logger.error("webdriver-manager not installed. Please install it with: pip install webdriver-manager")
                logger.error("Or download ChromeDriver manually from: https://chromedriver.chromium.org/")
                raise
            except Exception as e2:
                logger.error(f"Failed to initialize Chrome WebDriver with webdriver-manager: {e2}")
                logger.error("Please ensure Google Chrome is installed and try again")
                raise
    
    def login_to_website(self):
        """Login to akqaflicksph.com with credentials from .env file."""
        logger.info("Navigating to akqaflicksph.com...")
        
        try:
            self.driver.get("https://akqaflicksph.com")
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait a bit more for any dynamic content
            time.sleep(3)
            
            # First, try to find and click the button that reveals the login form
            logger.info("Looking for button to reveal login form...")
            
            try:
                # Look for the Vant UI button that was found in inspection
                dialog_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".van-button"))
                )
                logger.info("Found dialog button, clicking to reveal login form...")
                dialog_button.click()
                time.sleep(2)  # Wait for modal to appear
            except Exception as e:
                logger.warning(f"Could not find dialog button: {e}")
                # Continue anyway in case login form is already visible
            
            # Now look for login fields (they should be visible after clicking the button)
            logger.info("Looking for login fields...")
            
            # Look for common login field selectors (updated for modal context + Filipino)
            username_selectors = [
                "input[type='tel']",  # Phone number input (exact match from user)
                "input[placeholder='Ilagay ang Numero ng Telepono']",  # Exact Filipino placeholder
                "input[placeholder*='Numero ng Telepono']",  # Partial match
                "input[data-v-22bcd1bc][type='tel']",  # With specific data attribute
                "input[name='username']",
                "input[name='phone']",  # Phone number input
                "input[name='mobile']",  # Mobile number input
                "input[type='text']",  # Generic fallback
                "input[id*='phone']",
                "input[placeholder*='phone' i]",
                "input[placeholder*='mobile' i]",
                "input[placeholder*='numero' i]",  # Filipino for number
                "input[placeholder*='telepono' i]",  # Filipino for phone
                ".van-field input",  # Vant UI field input
                "#username",
                "#phone",
                "#mobile"
            ]
            
            password_selectors = [
                ".van-field__control",  # Exact class from user's inspection
                "input[placeholder='Ilagay ang Password sa Pag-login']",  # Exact Filipino placeholder
                "input[placeholder*='Password sa Pag-login']",  # Partial match
                "input[type='password']",
                "input[name='password']",
                "input[id*='password']",
                "input[placeholder*='password' i]",  # Case insensitive
                "input[placeholder*='kontrasenyas' i]",  # Filipino for password
                ".van-field input[type='password']",  # Vant UI password field
                "#password"
            ]
            
            username_field = None
            password_field = None
            
            # Try to find username field
            for selector in username_selectors:
                try:
                    username_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"Found username field with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            # Try to find password field - PRIORITIZE VISIBLE FIELDS WITH CORRECT PLACEHOLDER
            
            # Method 1: Find the visible password field with exact placeholder
            try:
                password_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[placeholder='Ilagay ang Password sa Pag-login']")
                for field in password_fields:
                    if field.is_displayed():
                        password_field = field
                        logger.info("Found visible password field with exact placeholder!")
                        break
            except Exception as e:
                logger.warning(f"Exact placeholder search failed: {e}")
            
            # Method 2: Find visible password input by type
            if not password_field:
                try:
                    password_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
                    for field in password_fields:
                        if field.is_displayed():
                            placeholder = field.get_attribute('placeholder') or ""
                            if 'Password' in placeholder:
                                password_field = field
                                logger.info(f"Found visible password field by type with placeholder: {placeholder}")
                                break
                except Exception as e:
                    logger.warning(f"Password type search failed: {e}")
            
            # Method 3: Find visible .van-field__control with password placeholder
            if not password_field:
                try:
                    van_fields = self.driver.find_elements(By.CSS_SELECTOR, ".van-field__control")
                    for field in van_fields:
                        if field.is_displayed():
                            placeholder = field.get_attribute('placeholder') or ""
                            field_type = field.get_attribute('type') or ""
                            if 'Password' in placeholder or field_type == 'password':
                                password_field = field
                                logger.info(f"Found visible van-field__control with placeholder: {placeholder}, type: {field_type}")
                                break
                except Exception as e:
                    logger.warning(f"Van-field search failed: {e}")
            
            # Fallback: Original logic for any remaining selectors
            if not password_field:
                for selector in password_selectors:
                    try:
                        password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if password_field.is_displayed():  # Add visibility check
                            logger.info(f"Found password field with selector: {selector}")
                            break
                        else:
                            logger.warning(f"Password field found with selector {selector} but not visible, continuing...")
                    except NoSuchElementException:
                        continue
            
            if not username_field or not password_field:
                logger.error("Could not find login fields after clicking button. Taking screenshot for debugging...")
                self.driver.save_screenshot("login_modal_debug.png")
                
                # Try to find any input fields for debugging
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                logger.info(f"Found {len(all_inputs)} input fields total:")
                for i, inp in enumerate(all_inputs):
                    inp_type = inp.get_attribute("type") or "text"
                    inp_name = inp.get_attribute("name") or "no-name"
                    inp_id = inp.get_attribute("id") or "no-id"
                    inp_placeholder = inp.get_attribute("placeholder") or "no-placeholder"
                    visible = inp.is_displayed()
                    logger.info(f"  Input {i+1}: type={inp_type}, name={inp_name}, id={inp_id}, placeholder={inp_placeholder}, visible={visible}")
                
                raise NoSuchElementException("Login fields not found")
            
            # Wait for fields to be interactable and scroll into view
            logger.info("Waiting for fields to be interactable...")
            
            try:
                # Wait for username field to be clickable
                username_field = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(username_field)
                )
                
                # Scroll to username field and ensure it's visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", username_field)
                time.sleep(1)
                
                # Try to focus the field first
                self.driver.execute_script("arguments[0].focus();", username_field)
                time.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Could not wait for username field to be clickable: {e}")
                # Continue with original field
            
            # Clear and enter credentials with enhanced interaction
            try:
                # Clear username field
                username_field.clear()
                username_field.send_keys(self.username)
                logger.info("Username entered")
            except Exception as e:
                logger.warning(f"Standard input failed for username, trying JavaScript: {e}")
                # Fallback to JavaScript
                self.driver.execute_script("arguments[0].value = arguments[1];", username_field, self.username)
                logger.info("Username entered via JavaScript")
            
            try:
                # Wait for password field to be interactable
                password_field = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(password_field)
                )
                
                # Scroll to password field
                self.driver.execute_script("arguments[0].scrollIntoView(true);", password_field)
                time.sleep(1)
                
                # Focus the field
                self.driver.execute_script("arguments[0].focus();", password_field)
                time.sleep(0.5)
                
                # Clear and enter password
                password_field.clear()
                password_field.send_keys(self.password)
                logger.info("Password entered via Standard send_keys()")
                password_method_used = "Standard send_keys()"
            except Exception as e:
                logger.warning(f"Standard input failed for password, trying JavaScript: {e}")
                # Advanced Vant UI / Vue.js password input methods
                logger.warning("Trying advanced Vant UI password input methods...")
                
                try:
                    # Method 4: Direct Vue.js property manipulation
                    logger.info("Attempting: Vue.js property manipulation method...")
                    self.driver.execute_script("""
                        var element = arguments[0];
                        var value = arguments[1];
                        
                        // Try to find Vue.js instance
                        var vueInstance = element.__vue__ || element._vnode || null;
                        if (vueInstance && vueInstance.$parent) {
                            try {
                                vueInstance.$parent.$data.password = value;
                                vueInstance.$parent.$forceUpdate();
                            } catch(e) {
                                console.log('Vue parent method failed:', e);
                            }
                        }
                        
                        // Set value and trigger all possible events
                        element.value = value;
                        element.setAttribute('value', value);
                        
                        // Simulate user typing with delay
                        setTimeout(function() {
                            var events = ['focus', 'input', 'change', 'keydown', 'keyup', 'blur', 'propertychange'];
                            events.forEach(function(eventType) {
                                var event;
                                if (eventType.includes('key')) {
                                    event = new KeyboardEvent(eventType, { bubbles: true, key: 'a' });
                                } else {
                                    event = new Event(eventType, { bubbles: true });
                                }
                                element.dispatchEvent(event);
                            });
                        }, 100);
                    """, password_field, self.password)
                    
                    # Wait and verify
                    time.sleep(2)
                    current_value = password_field.get_attribute("value") or ""
                    logger.info(f"Vue.js method result: '{current_value[:3]}***' (length: {len(current_value)})")
                    
                    if current_value == self.password:
                        logger.info("Password entered via Vue.js property manipulation")
                        password_method_used = "Vue.js property manipulation"
                    else:
                        # Method 5: Brute force DOM manipulation
                        logger.info("Attempting: Brute force DOM manipulation method...")
                        self.driver.execute_script("""
                            var element = arguments[0];
                            var value = arguments[1];
                            
                            // Multiple aggressive attempts
                            element.value = value;
                            element.defaultValue = value;
                            element.setAttribute('value', value);
                            element.textContent = value;
                            
                            // Try direct property setting
                            Object.defineProperty(element, 'value', {
                                value: value,
                                writable: true
                            });
                            
                            // Trigger Vue.js reactive system
                            if (element._vnode && element._vnode.componentInstance) {
                                element._vnode.componentInstance.$emit('input', value);
                            }
                            
                            // Force re-render
                            if (window.Vue) {
                                window.Vue.nextTick(function() {
                                    element.value = value;
                                });
                            }
                        """, password_field, self.password)
                        
                        # Check if brute force worked
                        time.sleep(1)
                        brute_force_value = password_field.get_attribute("value") or ""
                        logger.info(f"Brute force method result: '{brute_force_value[:3]}***' (length: {len(brute_force_value)})")
                        
                        if brute_force_value == self.password:
                            logger.info("Password entered via Brute force DOM manipulation")
                            password_method_used = "Brute force DOM manipulation"
                        else:
                            # Method 6: Character-by-character with events
                            logger.info("Attempting: Character-by-character input method...")
                            password_field.clear()
                            password_field.click()
                            time.sleep(0.5)
                            
                            for i, char in enumerate(self.password):
                                password_field.send_keys(char)
                                # Trigger input event after each character
                                self.driver.execute_script("""
                                    var element = arguments[0];
                                    var event = new Event('input', { bubbles: true });
                                    element.dispatchEvent(event);
                                """, password_field)
                                time.sleep(0.05)  # Small delay
                            
                            # Final verification
                            time.sleep(1)
                            final_value = password_field.get_attribute("value") or ""
                            logger.info(f"Character-by-character result: '{final_value[:3]}***' (length: {len(final_value)})")
                            
                            if final_value != self.password:
                                logger.error("All password input methods failed!")
                                logger.error("The Vant UI field might be read-only or have special protection")
                                raise Exception("Unable to set password field value")
                            else:
                                logger.info("Password entered via Character-by-character input")
                                password_method_used = "Character-by-character input"
                            
                except Exception as e3:
                    logger.error(f"All advanced password methods failed: {e3}")
                    raise
            
            # Log which password method was successful
            logger.info(f"Password method used: {password_method_used}")
            
            # Look for login button (updated for modal context + exact Filipino text)
            login_button_selectors = [
                "button:contains('Mag-log in Ngayon')",  # Exact Filipino text from user
                "button .van-button__text:contains('Mag-log in Ngayon')",  # Text within span
                ".van-button--danger.van-button--large.van-button--block.van-button--round",  # Exact classes
                "button[data-v-22bcd1bc].van-button.van-button--danger",  # With data attribute
                "button[type='submit']",
                "input[type='submit']",
                ".van-button[type='submit']",  # Vant UI submit button
                ".van-dialog__confirm",  # Vant UI dialog confirm button
                "button:contains('Mag-login')",  # Filipino for login
                "button:contains('Login')",
                "button:contains('Sign In')",
                "button:contains('Pumasok')",  # Filipino for enter/sign in
                "input[value*='Mag-login']",  # Filipino
                "#login-button",
                "#submit",
                ".login-button",
                ".submit-button"
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    if ":contains" in selector:
                        # Use XPath for text content
                        text = selector.split("'")[1]
                        xpath = f"//button[contains(text(), '{text}')]"
                        login_button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"Found login button with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not login_button:
                logger.warning("Could not find login button, trying to submit form")
                password_field.submit()
            else:
                try:
                    # Wait for login button to be clickable
                    login_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(login_button)
                    )
                    
                    # Scroll to button and ensure it's visible
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
                    time.sleep(1)
                    
                    # Try standard click first
                    login_button.click()
                    logger.info("Login button clicked successfully")
                except Exception as e:
                    logger.warning(f"Standard click failed for login button, trying JavaScript: {e}")
                    try:
                        # Fallback to JavaScript click
                        self.driver.execute_script("arguments[0].click();", login_button)
                        logger.info("Login button clicked via JavaScript")
                    except Exception as e2:
                        logger.error(f"JavaScript click also failed: {e2}")
                        # Final fallback - try submitting the form
                        try:
                            password_field.submit()
                            logger.info("Form submitted via password field")
                        except Exception as e3:
                            logger.error(f"Form submit also failed: {e3}")
                            raise
            
            logger.info("Login form submitted")
            
            # Wait for toast message to appear and check for errors
            logger.info("Checking for error toast messages...")
            time.sleep(2)  # Wait for toast to appear
            
            # Check for toast error messages
            try:
                toast_elements = self.driver.find_elements(By.CSS_SELECTOR, ".van-toast")
                
                for toast in toast_elements:
                    # Check if toast is visible (not display: none)
                    toast_style = toast.get_attribute("style") or ""
                    is_visible = "display: none" not in toast_style and toast.is_displayed()
                    
                    if is_visible:
                        toast_text = toast.text.strip()
                        logger.warning(f"Toast message detected: '{toast_text}'")
                        
                        # Check for Filipino error messages
                        filipino_errors = [
                            "Ilagay ang Password sa Pag-login",  # Enter the password for login
                            "Ilagay ang Numero ng Telepono",    # Enter the phone number
                            "Mali ang Password",                 # Wrong password
                            "Mali ang Numero",                   # Wrong number
                            "Hindi mahanap ang account",         # Account not found
                            "Nabigo ang pag-login"              # Login failed
                        ]
                        
                        # Check for English error messages
                        english_errors = [
                            "Please enter password",
                            "Please enter phone number", 
                            "Please enter username",
                            "Wrong password",
                            "Wrong number",
                            "Account not found",
                            "Login failed",
                            "Invalid credentials"
                        ]
                        
                        # Check if toast contains error message
                        is_error = False
                        for error_msg in filipino_errors + english_errors:
                            if error_msg.lower() in toast_text.lower():
                                logger.error(f"Login error detected in toast: '{error_msg}'")
                                logger.error(f"Full toast message: '{toast_text}'")
                                is_error = True
                                break
                        
                        if is_error:
                            # Take screenshot for debugging
                            self.driver.save_screenshot("login_error_toast_debug.png")
                            logger.error("Login failed due to toast error message")
                            logger.error("Check login_error_toast_debug.png for visual confirmation")
                            
                            # Specific handling for password vs username errors
                            if "password" in toast_text.lower() or "Password" in toast_text:
                                logger.error("PASSWORD FIELD ERROR: Password was not entered correctly")
                                logger.error("Debugging password field interaction...")
                                
                                # Debug password field
                                try:
                                    password_field = self.driver.find_element(By.CSS_SELECTOR, ".van-field__control")
                                    current_value = password_field.get_attribute("value") or ""
                                    logger.error(f"Current password field value: '{current_value}'")
                                    logger.error(f"Expected password: '{self.password}'")
                                    if current_value != self.password:
                                        logger.error("PASSWORD NOT SET CORRECTLY - this explains the login failure")
                                except Exception as e:
                                    logger.error(f"Could not debug password field: {e}")
                            
                            elif "telepono" in toast_text.lower() or "numero" in toast_text.lower() or "phone" in toast_text.lower():
                                logger.error("USERNAME/PHONE FIELD ERROR: Phone number was not entered correctly")
                            
                            raise Exception(f"Login failed with toast error: {toast_text}")
                        
            except Exception as e:
                if "Login failed with toast error" in str(e):
                    raise  # Re-raise the login error
                else:
                    logger.warning(f"Could not check toast messages: {e}")
            
            # Wait for page to change after login and check for success/failure
            logger.info("Checking login result...")
            time.sleep(3)  # Additional wait for page response
            
            # Check for login success indicators (URL change, dashboard elements, etc.)
            current_url = self.driver.current_url
            logger.info(f"Current URL after login: {current_url}")
            
            # Check for error messages in Filipino/English
            error_indicators = [
                "error", "mali", "wrong", "invalid", "hindi tama", "unauthorized", 
                "failed", "nabigo", "incorrect", "maling", "access denied"
            ]
            
            page_text = self.driver.page_source.lower()
            login_failed = False
            
            for error_term in error_indicators:
                if error_term in page_text:
                    logger.error(f"Login error detected: '{error_term}' found in page")
                    login_failed = True
                    break
            
            # Check if we're still on the login modal (indicates failure)
            try:
                still_on_login = self.driver.find_elements(By.CSS_SELECTOR, ".van-dialog__confirm")
                if still_on_login and any(elem.is_displayed() for elem in still_on_login):
                    logger.error("Still on login modal - login likely failed")
                    login_failed = True
            except:
                pass
            
            # Check for success indicators
            success_indicators = [
                "task hall", "home", "welcome", "matagumpay", "internship",
                "piliin ang wika"
            ]
            
            login_success = False
            for success_term in success_indicators:
                if success_term in page_text:
                    logger.info(f"Login success indicator found: '{success_term}'")
                    login_success = True
                    break
            
            if login_failed:
                logger.error("Login appears to have failed")
                logger.error("Please check your credentials in the .env file")
                logger.error("Also check login_result_debug.png for visual confirmation")
                raise Exception("Login failed - check credentials and login_result_debug.png")
            elif login_success:
                logger.info("Login appears to have succeeded!")
            else:
                logger.warning("Login result unclear - continuing anyway")
                logger.warning("Check login_result_debug.png to verify login status")
            
            # Wait for page to change after login
            time.sleep(3)
            
        except TimeoutException:
            logger.error("Timeout while loading the website")
            raise
        except Exception as e:
            logger.error(f"Error during login: {e}")
            raise
    
    def change_language_to_english(self):
        """Change the website language to English."""
        logger.info("Changing language to English...")
        
        max_attempts = 3
        attempt = 1
        
        while attempt <= max_attempts:
            try:
                logger.info(f"Attempt {attempt} of {max_attempts} to change language to English...")
                
                # Wait for page to load after login
                time.sleep(3)
                
                # Check if language is already English by looking for Piliin ang Wika
                try:
                    language_button = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Piliin ang Wika')]"))
                    )
                    # If we find Piliin ang Wika, we need to change the language
                    logger.info("Found 'Piliin ang Wika' - need to change language...")
                except:
                    # If we don't find it, language is probably already English
                    logger.info("'Piliin ang Wika' not found - language appears to be English already")
                    return
                
                # Click the language selector in navbar
                logger.info("Looking for language selector in navbar...")
                language_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Piliin ang Wika')]"))
                )
                language_button.click()
                logger.info("Language selector clicked")
                
                # Wait for language selection page to load
                WebDriverWait(self.driver, 10).until(
                    EC.url_contains("#/language")
                )
                logger.info("Language selection page loaded")
                time.sleep(2)
                
                # Click on English option
                logger.info("Looking for English language option...")
                english_option = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'van-cell--clickable')]//span[text()='English']"))
                )
                english_option.click()
                logger.info("English language selected")
                
                # Wait for page to return to home
                time.sleep(3)
                
                # Verify language changed by checking Piliin ang Wika is gone
                try:
                    WebDriverWait(self.driver, 5).until_not(
                        EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Piliin ang Wika')]"))
                    )
                    logger.info("✅ Language successfully changed to English!")
                    return
                except:
                    logger.warning("Language may not have changed successfully")
                    attempt += 1
                    continue
                    
            except Exception as e:
                logger.error(f"Error changing language to English (attempt {attempt}): {e}")
                attempt += 1
                continue
        
        logger.error(f"Failed to change language to English after {max_attempts} attempts")
        logger.warning("Continuing with current language...")
    
    def check_account_identity(self):
        """Check the account identity (Internship, VIP1, VIP2, etc.) to know which button to click."""
        logger.info("Checking account identity...")

        try:
            # Navigate to Account page via footer
            logger.info("Navigating to Account page...")
            account_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#/user']"))
            )
            account_link.click()
            
            # Wait for account page to load
            time.sleep(3)
            
            # Check account identity
            logger.info("Looking for account identity...")
            identity_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div//p[text()='Your Identity']/following-sibling::p"))
            )
            
            identity_text = identity_element.text.strip()
            logger.info(f"Account identity found: {identity_text}")
            
            # Extract just the identity name (remove any extra text)
            identity_options = ["Internship", "VIP1", "VIP2", "VIP3", "VIP4", "VIP5", "VIP6", "VIP7", "VIP8", "VIP9"]
            user_identity = None
            
            for option in identity_options:
                if option in identity_text:
                    user_identity = option
                    break
            
            if not user_identity:
                logger.warning(f"Could not parse identity from: {identity_text}")
                user_identity = self.default_identity
            
            logger.info(f"User identity determined: {user_identity}")
            return user_identity
            
        except Exception as e:
            logger.error(f"Error checking account identity: {e}")
            logger.warning("Defaulting to Internship")
            return self.default_identity
    
    def navigate_to_task_button(self, identity):
        """Navigate back to home and click the appropriate task button based on identity."""
        logger.info(f"Navigating to task button for identity: {identity}")
        
        try:
            # Navigate back to Home page via footer
            logger.info("Navigating back to Home page...")
            home_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#/']"))
            )
            home_link.click()
            
            # Wait for home page to load
            time.sleep(3)
            
            # Find the TaskHall container
            logger.info("Looking for TaskHall container...")
            task_hall = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".TaskHall"))
            )
            
            # Look for the specific task button based on identity
            logger.info(f"Looking for {identity} button...")
            task_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//div[@class='TaskHall']//div[contains(@class, 'van-grid-item__content') and contains(text(), '{identity}')]"))
            )
            
            # Scroll to the button and click it
            self.driver.execute_script("arguments[0].scrollIntoView(true);", task_button)
            time.sleep(1)
            
            task_button.click()
            logger.info(f"{identity} button clicked successfully")

            # Store URL after clicking the task button
            self.task_url = self.driver.current_url
            while "taskList" not in self.task_url:
                self.task_url = self.driver.current_url
                time.sleep(1)
            logger.info(f"URL after clicking {identity} button: {self.task_url}")
            
        except Exception as e:
            logger.error(f"Error navigating to task button: {e}")
            logger.info("Trying fallback method...")
            
            # Fallback: try to find any available task button
            try:
                fallback_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".TaskHall .van-grid-item__content"))
                )
                fallback_button.click()
                logger.info("Fallback task button clicked")
            except Exception as e2:
                logger.error(f"Fallback method also failed: {e2}")
                raise
    
    def setup_task_prerequisites(self):
        """Updated method that implements the full workflow: change language, check identity, click appropriate button."""
        logger.info("Setting up task prerequisites...")
        
        try:
            # Step 1: Change language to English
            self.change_language_to_english()
            
            # Step 2: Check account identity
            user_identity = self.check_account_identity()
            
            # Step 3: Navigate to appropriate task button
            self.navigate_to_task_button(user_identity)
            
            logger.info("Task prerequisites setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error in task prerequisites setup: {e}")
            raise
    
    def start_tasks(self) -> bool:
        """Execute the main task automation loop, completing tasks until none are left or progress stalls."""
        logger.info("Starting task execution loop...")
        
        stalled_attempts = 0
        max_stalled_attempts = 3
        last_tasks_remaining = -1  # Use -1 to indicate the first run
        tasks_completed = 0

        while stalled_attempts < max_stalled_attempts:
            logger.info(f"--- Starting task cycle (Stalled attempts: {stalled_attempts}/{max_stalled_attempts}) ---")
            
            try:
                # Wait for task page to load
                time.sleep(3)
                
                # Check remaining tasks
                logger.info("Checking tasks remaining...")
                tasks_remaining = -1
                try:
                    tasks_remaining_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//span[text()='Tasks Remaining Today']/preceding-sibling::div//span"))
                    )
                    tasks_remaining = int(tasks_remaining_element.text.strip())
                    logger.info(f"Tasks remaining today: {tasks_remaining}")
                except Exception as e:
                    logger.error(f"Could not read tasks remaining: {e}")
                    self.driver.save_screenshot("tasks_remaining_debug.png")
                    stalled_attempts += 1
                    logger.warning(f"Error reading task count is considered a stalled attempt. Count: {stalled_attempts}")
                    continue

                # Check if all tasks are completed
                if tasks_remaining == 0:
                    logger.info("🎉 All tasks are completed for today! Nothing to do.")
                    return False if tasks_completed == 0 else True

                # Check for stalled progress. This is the core logic.
                if last_tasks_remaining != -1 and tasks_remaining >= last_tasks_remaining:
                    stalled_attempts += 1
                    logger.warning(f"⚠️  Task count did not decrease. Stalled attempt count is now {stalled_attempts}.")
                else:
                    # Progress was made or it's the first run, so reset the counter.
                    stalled_attempts = 0
                
                # Update task count for the next iteration's check
                last_tasks_remaining = tasks_remaining

                if stalled_attempts >= max_stalled_attempts:
                    logger.error(f"❌ Task loop stalled for {max_stalled_attempts} attempts. Aborting task process.")
                    break

                logger.info(f"Proceeding with task execution for one task...")
                
                # Find available task items using the correct structure
                try:
                    logger.info("🔍 Looking for task items in correct structure...")
                    task_selector = ".task-list .van-list .van-grid .van-grid-item"
                    
                    try:
                        task_items = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, task_selector))
                        )
                        
                        valid_task_items = [
                            item for item in task_items 
                            if item.is_displayed() and item.is_enabled() and item.find_elements(By.TAG_NAME, "img")
                        ]
                        
                        if not valid_task_items:
                            raise Exception("No valid task items with thumbnails found")
                        
                        logger.info(f"📋 Found {len(valid_task_items)} valid task items, clicking the first one.")
                        first_task = valid_task_items[0]
                        
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", first_task)
                            time.sleep(1)
                            first_task.click()
                        except Exception as e:
                            self.driver.execute_script("arguments[0].click();", first_task)
                        
                        time.sleep(3)
                        
                        new_url = self.driver.current_url
                        logger.info(f"📍 New URL after click: {new_url}")
                        
                        if "/task/video/" in new_url:
                            logger.info("✅ Navigated to video page. Handling video...")
                            self.handle_video_and_submit()
                            tasks_completed += 1
                            continue
                        
                        elif "/myTask" in new_url:
                            logger.info("📍 Redirected to myTask page. Handling in-progress task...")
                            try:
                                pane = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".van-tabs__content .van-tab__pane:first-child")))
                                cell = pane.find_element(By.CSS_SELECTOR, ".van-list .van-cell .TaskItem")
                                button = cell.find_element(By.CSS_SELECTOR, "button")
                                
                                if "submit" in button.text.lower():
                                    button.click()
                                    time.sleep(3)
                                    if "/task/video/" in self.driver.current_url:
                                        self.handle_video_and_submit()
                                        tasks_completed += 1
                                        continue
                                    else:
                                        raise Exception("Did not navigate to video page after clicking 'Submit' on in-progress task.")
                                else:
                                    raise Exception(f"Button in in-progress task was not 'Submit', but '{button.text}'.")
                            except Exception as e_inner:
                                raise Exception(f"Failed to process in-progress task: {e_inner}")
                        
                        else:
                            raise Exception(f"Unexpected URL after task click: {new_url}")
                    
                    except Exception as e:
                        logger.error(f"Error finding or clicking task items: {e}")
                        self.driver.save_screenshot("task_selection_debug.png")
                        raise  # Raise to trigger the outer exception handler
                
                except Exception as e:
                    logger.error(f"❌ Complete task selection failed: {e}")
                    raise # Raise to trigger the outer exception handler
            
            except Exception as e:
                stalled_attempts += 1
                logger.error(f"Error during task execution loop: {e}")
                logger.error(f"This error counts as stalled attempt {stalled_attempts}/{max_stalled_attempts}.")
                self.driver.save_screenshot("task_loop_error_debug.png")
                # Attempt to recover by navigating back to the task list page
                try:
                    self.navigate_to_task_list()
                except Exception as nav_e:
                    logger.error(f"Could not navigate back to task list page to recover: {nav_e}")

        if stalled_attempts >= max_stalled_attempts:
            logger.warning(f"Exiting task loop because progress stalled for {max_stalled_attempts} consecutive attempts.")
            return False
        else:
            logger.info("Task loop completed successfully.")
            return True
    
    def navigate_to_task_list(self):
        """Navigate to the task list page."""
        # Return if already on task list page
        if "taskList" in self.driver.current_url:
            return

        logger.info("Navigating to task list page...")
        self.driver.get(self.task_url)

        # Wait for task list page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".task-list .van-list .van-grid .van-grid-item"))
        )

    def handle_video_and_submit(self):
        """Improved video handling with VideoJS support and dynamic status monitoring."""
        logger.info("🎬 Starting improved video handling...")
        
        try:
            # Step 1: Detect and start video
            self.start_video_playback()
            
            # Step 2: Monitor watch progress 
            required_seconds = self.monitor_video_progress()
            
            # Step 3: Submit task when ready
            self.submit_completed_task()
            
        except Exception as e:
            logger.error(f"Error in video handling: {e}")
            raise

    def start_video_playback(self):
        """Detect and start video playback, with specific VideoJS support."""
        logger.info("🔍 Detecting video player type...")
        
        try:
            # First, check for VideoJS player (like in user's example)
            videojs_selectors = [
                ".video-js .vjs-big-play-button",      # Big play button
                ".video-js .vjs-play-control",         # Control bar play button
                ".vjs-big-play-button",                # Just the big play button
                ".vjs-play-control",                   # Just the control play button
            ]
            
            video_started = False
            
            # Try VideoJS-specific selectors first
            for selector in videojs_selectors:
                try:
                    play_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    logger.info(f"✅ Found VideoJS play button: {selector}")
                    
                    # Scroll to button and click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", play_button)
                    time.sleep(1)
                    
                    # Try clicking the button
                    try:
                        play_button.click()
                        logger.info("🎬 VideoJS play button clicked successfully")
                        video_started = True
                        break
                    except Exception as e:
                        logger.warning(f"Standard click failed, trying JavaScript: {e}")
                        try:
                            self.driver.execute_script("arguments[0].click();", play_button)
                            logger.info("🎬 VideoJS play button clicked via JavaScript")
                            video_started = True
                            break
                        except Exception as e2:
                            logger.warning(f"JavaScript click also failed: {e2}")
                            continue
                            
                except TimeoutException:
                    continue
                except Exception as e:
                    logger.warning(f"Error with selector {selector}: {e}")
                    continue
            
            # If VideoJS didn't work, try generic video elements
            if not video_started:
                logger.info("🔍 VideoJS not found, trying generic video elements...")
                
                generic_selectors = [
                    "video",                           # HTML5 video element
                    ".video-player",                   # Generic video player
                    ".play-button",                    # Generic play button
                    "[class*='play-btn']",            # Play button variations
                    "[class*='video-play']",          # Video play variations
                    "button[aria-label*='play']",     # Accessible play buttons
                    "button[title*='play']",          # Play buttons with titles
                ]
                
                for selector in generic_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        for element in elements:
                            if element.is_displayed():
                                try:
                                    # For video elements, try to trigger play
                                    if element.tag_name.lower() == 'video':
                                        self.driver.execute_script("arguments[0].play();", element)
                                        logger.info("🎬 Video started via JavaScript play()")
                                        video_started = True
                                        break
                                    else:
                                        # For buttons, try clicking
                                        element.click()
                                        logger.info(f"🎬 Generic play button clicked: {selector}")
                                        video_started = True
                                        break
                                except Exception as e:
                                    logger.warning(f"Could not interact with element: {e}")
                                    continue
                        
                        if video_started:
                            break
                            
                    except Exception as e:
                        logger.warning(f"Error with generic selector {selector}: {e}")
                        continue
            
            # Final fallback - check if video is already playing
            if not video_started:
                logger.warning("⚠️  Could not find or click play button")
                logger.info("🔍 Checking if video is already playing...")
                
                # Wait a moment and check for status text
                time.sleep(2)
                
                # Look for "Currently watched" text to see if video is playing
                try:
                    status_element = self.driver.find_element(By.XPATH, 
                        "//p[contains(text(), 'Currently watched')]")
                    if status_element:
                        logger.info("✅ Video appears to be playing already (status text found)")
                        video_started = True
                except:
                    logger.warning("❌ No video status found - video may not be playing")
            
            # Give video time to start
            if video_started:
                logger.info("⏳ Waiting for video to start...")
                time.sleep(3)
            else:
                logger.warning("⚠️  Video playback status uncertain - continuing anyway...")
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"Error starting video playback: {e}")
            logger.warning("Continuing with monitoring anyway...")

    def monitor_video_progress(self):
        """Monitor video progress using 'Currently watched x seconds' status."""
        logger.info("📊 Monitoring video watch progress...")
        
        try:
            # First, try to find the task requirements to know how many seconds are needed
            required_seconds = 10  # Default fallback
            
            try:
                # Look for task requirements like "Watch 10 seconds"
                requirement_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, 
                        "//p[contains(text(), 'Watch') and contains(text(), 'seconds')]"))
                )
                
                requirement_text = requirement_element.text
                logger.info(f"📋 Found task requirement: {requirement_text}")
                
                # Extract number from text like "Watch 10 seconds"
                import re
                numbers = re.findall(r'\d+', requirement_text)
                if numbers:
                    required_seconds = int(numbers[0])
                    logger.info(f"🎯 Required watch time: {required_seconds} seconds")
                    
            except Exception as e:
                logger.warning(f"Could not find task requirements: {e}")
                logger.info(f"Using default requirement: {required_seconds} seconds")
            
            # Monitor progress for up to 600 seconds total
            max_wait_time = 600
            start_time = time.time()
            watched_seconds = 0
            last_watched = 0
            
            logger.info("⏱️  Starting progress monitoring...")
            
            while time.time() - start_time < max_wait_time:
                try:
                    # Look for status text like "Currently watched 13 seconds"
                    status_elements = self.driver.find_elements(By.XPATH, 
                        "//p[contains(text(), 'Currently watched') and contains(text(), 'seconds')]")
                    
                    if status_elements:
                        status_text = status_elements[0].text
                        
                        # Extract watched seconds from text like "Currently watched 13 seconds"
                        import re
                        numbers = re.findall(r'Currently watched (\d+)', status_text)
                        if numbers:
                            watched_seconds = int(numbers[0])
                            
                            # Only log when seconds change to avoid spam
                            if watched_seconds != last_watched:
                                logger.info(f"⏱️  Progress: {watched_seconds}/{required_seconds} seconds watched")
                                last_watched = watched_seconds
                            
                            # Check if we've met the requirement
                            if watched_seconds >= required_seconds:
                                logger.info(f"✅ Required watch time achieved! ({watched_seconds} >= {required_seconds})")
                                return required_seconds
                    else:
                        # No status found - log periodically
                        elapsed = int(time.time() - start_time)
                        if elapsed % 5 == 0 and elapsed > 0:  # Every 5 seconds
                            logger.info(f"⏳ No progress status found - elapsed: {elapsed}s")
                    
                    time.sleep(1)  # Check every second
                    
                except Exception as e:
                    logger.warning(f"Error checking progress: {e}")
                    time.sleep(2)
                    continue
            
            # Timeout reached
            logger.warning(f"⚠️  Timeout reached after {max_wait_time}s")
            logger.info(f"📊 Final watched time: {watched_seconds} seconds")
            
            if watched_seconds >= required_seconds:
                logger.info("✅ Requirement met despite timeout")
                return required_seconds
            else:
                logger.warning(f"⚠️  May not have met requirement ({watched_seconds} < {required_seconds})")
                logger.info("Proceeding to submit anyway...")
                return watched_seconds
                
        except Exception as e:
            logger.error(f"Error monitoring video progress: {e}")
            logger.warning("Falling back to fixed 12-second wait...")
            
            # Fallback to old method
            for i in range(12, 0, -1):
                logger.info(f"⏱️  Fallback timer: {i} seconds remaining...")
                time.sleep(1)
            
            return 12

    def submit_completed_task(self):
        """Find and click the Submit Complete Task button."""
        logger.info("🔍 Looking for Submit Complete Task button...")
        
        try:
            # Specific selectors for the Submit Complete Task button
            submit_selectors = [
                # Exact text match (most reliable)
                "//button[contains(text(), 'Submit Complete Task')]",
                "//span[contains(text(), 'Submit Complete Task')]/ancestor::button",
                "//div[contains(text(), 'Submit Complete Task')]/ancestor::button",
                
                # Van UI button with specific text
                ".van-button .van-button__text[text()='Submit Complete Task']/..",
                ".van-button:has(.van-button__text:contains('Submit Complete Task'))",
                
                # More generic variations
                "//button[contains(text(), 'Submit Complete')]",
                "//button[contains(text(), 'Complete Task')]",
                "//button[contains(text(), 'Submit Task')]",
                
                # Class-based selectors from user's example
                ".button-container .mybutton",  # The specific "mybutton" class
                ".van-button.mybutton",
                
                # Generic submit patterns
                "//button[contains(text(), 'Submit')]",
                "//button[contains(text(), 'submit')]",
                "//button[contains(text(), 'SUBMIT')]",
                "//input[@type='submit']",
                "//button[@type='submit']",
                ".submit-button",
                ".submit-btn",
                "[class*='submit']",
            ]
            
            submit_button = None
            
            # Try each selector
            for selector in submit_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath selector
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        # CSS selector
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    # Check each found element
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Additional verification - make sure it's not the "reset Task" button
                            element_text = element.text.lower()
                            if 'reset' in element_text:
                                logger.info(f"⏭️  Skipping reset button: {element.text}")
                                continue
                                
                            submit_button = element
                            logger.info(f"✅ Found Submit button: '{element.text}' with selector: {selector}")
                            break
                    
                    if submit_button:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error with selector {selector}: {e}")
                    continue
            
            if not submit_button:
                logger.error("❌ Could not find Submit Complete Task button")
                
                # Save debug screenshot
                self.driver.save_screenshot("submit_button_debug.png")
                logger.info("Debug screenshot saved as: submit_button_debug.png")
                
                # Try to list all buttons for debugging
                try:
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    logger.info(f"🔍 Found {len(all_buttons)} buttons on page:")
                    for i, button in enumerate(all_buttons):
                        if button.is_displayed():
                            text = button.text.strip() or button.get_attribute("aria-label") or button.get_attribute("title") or f"button-{i}"
                            logger.info(f"  {i+1}. '{text}' (classes: {button.get_attribute('class')})")
                except:
                    pass
                
                raise Exception("Submit Complete Task button not found")
            
            # Click the submit button
            logger.info("🎯 Clicking Submit Complete Task button...")
            
            try:
                # Scroll to button and ensure it's visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                time.sleep(1)
                
                # Try standard click first
                submit_button.click()
                logger.info("✅ Submit button clicked successfully")
                
            except Exception as e:
                logger.warning(f"Standard click failed, trying JavaScript: {e}")
                try:
                    # Fallback to JavaScript click
                    self.driver.execute_script("arguments[0].click();", submit_button)
                    logger.info("✅ Submit button clicked via JavaScript")
                except Exception as e2:
                    logger.error(f"JavaScript click also failed: {e2}")
                    raise
            
            # Wait for submission to process
            logger.info("⏳ Waiting for task submission to process...")
            
            try:
                # Wait until the URL no longer contains '/task/video/' or changes to a known task list/home
                WebDriverWait(self.driver, 15).until_not(
                    EC.url_contains('/task/video/')
                )
                logger.info(f"✅ Navigated away from video page. Current URL: {self.driver.current_url}")
            except TimeoutException:
                logger.warning("⚠️  Timed out waiting for URL to change from video page after submission.")
                logger.warning(f"Current URL is still: {self.driver.current_url}")
                logger.warning("Proceeding, but next steps might be affected.")
            
            # Try to detect success/completion message
            try:
                success_messages = [
                    "//div[contains(@class, 'van-toast') and not(contains(@style, 'display: none')) and .//span[text()='Success']]"
                ]
                
                for msg_selector in success_messages:
                    try:
                        success_element = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, msg_selector))
                        )
                        logger.info(f"✅ Success message detected: {success_element.text}")
                        break
                    except TimeoutException:
                        continue
                        
            except Exception as e:
                logger.info("No specific success message detected (this may be normal)")
            
            logger.info("🎉 Task submission completed!")
            
        except Exception as e:
            logger.error(f"Error submitting task: {e}")
            raise

    def wait_and_screenshot(self):
        """Take screenshots of task list page."""
        logger.info("Taking screenshots of task list page...")
        time.sleep(5);
        try:
            # Navigate to task list
            self.navigate_to_task_list()

            logger.info("Waiting for all images to load before taking screenshot...")
            # Wait for all images to load (up to 10 seconds)
            max_wait = 10
            poll_interval = 0.5
            waited = 0
            while waited < max_wait:
                all_loaded = self.driver.execute_script(
                    "return Array.from(document.images).every(img => img.complete && img.naturalWidth > 0);"
                )
                if all_loaded:
                    logger.info("All images loaded.")
                    break
                time.sleep(poll_interval)
                waited += poll_interval
            else:
                logger.warning("Timeout waiting for all images to load. Proceeding with screenshot.")

            logger.info("Checking tasks completed...")
            try:
                tasks_completed_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[text()='Tasks Completed Today']/preceding-sibling::div//span"))
                )
                tasks_completed = int(tasks_completed_element.text.strip())
                logger.info(f"Tasks completed today: {tasks_completed}")
            except Exception as e:
                logger.error(f"Error checking tasks completed: {e}")
                raise Exception("Tasks completed today not found")
            # Take screenshot of current tasks page
            logger.info("Taking screenshot of tasks page...")
            tasks_screenshot_path = 'tasks_screenshot.png'
            self.driver.save_screenshot(tasks_screenshot_path)
            logger.info(f"Tasks page screenshot saved as: {tasks_screenshot_path}")

            # Verify if the saved screenshot contains the text '5 Tasks Completed Today' with tesseract
            logger.info("Verifying if the screenshot contains the text '5 Tasks Completed Today' with tesseract...")
            import pytesseract
            screenshot = Image.open(tasks_screenshot_path).crop((720,100,1420,325))
            # Convert PIL Image to OpenCV format
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            img = cv2.resize(img, None, fx=2, fy=2)  # Scale up for better OCR
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            cv2.imwrite("debug_tasks_screenshot.png", img)
            print("Debug screenshot saved as 'debug_tasks_screenshot.png'")


            found_text = False
            # Test different PSM modes
            for psm in [6, 11]:
                config = f'--oem 3 --psm {psm}'
                screenshot_text = pytesseract.image_to_string(screenshot, config=config).strip().replace('\n', '').replace('\r', '')
                logger.info(f"Tasks page screenshot text with PSM {psm}: {screenshot_text}")
                if f'{tasks_completed}Tasks Completed Today' in screenshot_text:
                    logger.info(f"✅ Tasks page screenshot contains the text '{tasks_completed} Tasks Completed Today' with PSM {psm}")
                    found_text = True
                    break
                else:
                    logger.warning(f"❌ Tasks page screenshot does not contain the text '{tasks_completed} Tasks Completed Today' with PSM {psm}")

            if not found_text:
                logger.error(f"❌ Tasks page screenshot does not contain the text '{tasks_completed} Tasks Completed Today'")
                raise Exception(f"Tasks page screenshot does not contain the text '{tasks_completed} Tasks Completed Today'")
            
            # Store screenshot paths for later use
            self.tasks_screenshot = tasks_screenshot_path
            
            logger.info("Screenshots taken successfully")
            
        except Exception as e:
            logger.error(f"Error taking screenshots: {e}")
            raise
    
    def detect_os(self):
        """Detect the operating system."""
        os_name = platform.system().lower()
        logger.info(f"Detected operating system: {os_name}")
        return os_name
    
    def is_whatsapp_visible(self):
        """Check if WhatsApp is visible on screen using multiple detection methods."""
        if self.is_macos:
            if not self.permissions_utility_available:
                logger.warning("Screenshot permission check utility not available at startup. Assuming manual verification for WhatsApp visibility.")
                return False
            # No direct return if screenshot_permission_granted is false, proceed to process check.

        logger.info("Checking if WhatsApp is visible on screen...")

        # Method 1: Process detection (macOS only - most reliable)
        if self.is_macos:
            try:
                logger.info("Attempting macOS process detection for WhatsApp...")
                result = subprocess.run([
                    'osascript', '-e',
                    'tell application "System Events" to get name of (processes whose background only is false and name is "WhatsApp")'
                ], capture_output=True, text=True, timeout=3) # Check specifically for "WhatsApp"
                
                if result.returncode == 0 and "whatsapp" in result.stdout.lower():
                    logger.info("✅ WhatsApp detected via process list (osascript).")
                    return True
                elif result.returncode == 0 and not result.stdout.strip():
                    logger.info("macOS process detection: WhatsApp process not found.")
                else:
                    logger.warning(f"macOS process detection failed or WhatsApp not found. stdout: {result.stdout.strip()}, stderr: {result.stderr.strip()}")
                    
            except subprocess.TimeoutExpired:
                logger.warning("macOS process detection for WhatsApp timed out.")
            except Exception as e:
                logger.warning(f"macOS process detection for WhatsApp failed: {e}")
        
        # If not on macOS or process check failed/not applicable, proceed to visual checks
        # Visual checks require screenshot permission
        if self.is_macos and not self.screenshot_permission_granted:
            logger.warning("Screen Recording permission not granted (checked at startup). Skipping visual WhatsApp detection.")
            logger.warning("Relying on manual verification if WhatsApp opening fails.")
            return False # Cannot perform visual checks

        try:
            # Take a screenshot of the current screen
            # This part is common for subsequent visual checks
            logger.info("Taking screenshot for visual WhatsApp detection...")
            screenshot = pyautogui.screenshot()
            
            # Method 2: Look for WhatsApp's distinctive green color
            try:
                logger.info("Attempting color signature detection for WhatsApp...")
                whatsapp_green = (37, 211, 102)  # RGB values for WhatsApp green
                tolerance = 30  # Color tolerance
                
                width, height = screenshot.size
                sample_points = [
                    (width // 4, height // 10),    # Top area
                    (width // 10, height // 4),    # Left area
                    (width // 2, height // 10),    # Top center
                    (50, 50),                      # Top-left corner
                    (100, 100),                    # Search area (typical in desktop app)
                ]
                
                green_pixels_found = 0
                for x, y in sample_points:
                    if 0 <= x < width and 0 <= y < height: # Ensure points are within bounds
                        pixel = screenshot.getpixel((x, y))
                        if len(pixel) >= 3 and all(abs(pixel[i] - whatsapp_green[i]) <= tolerance for i in range(3)):
                            green_pixels_found += 1
                
                if green_pixels_found >= 2:
                    logger.info("✅ WhatsApp detected via color signature.")
                    return True
                else:
                    logger.info("Color signature for WhatsApp not strongly detected.")
                    
            except Exception as e:
                logger.warning(f"Color detection for WhatsApp failed: {e}")

            # Method 3: Look for WhatsApp-specific text/elements (OCR - Last Resort)
            logger.info("Attempting OCR text detection for WhatsApp (last resort)...")
            whatsapp_indicators = [
                'WhatsApp',
                'Chats',
            ]
            
            try:
                import pytesseract
                screenshot = pyautogui.screenshot(region=(0,0,145,80))
                screenshot_text = pytesseract.image_to_string(screenshot, lang='eng')
                
                for indicator in whatsapp_indicators:
                    if indicator.lower() in screenshot_text.lower():
                        logger.info(f"✅ WhatsApp detected via text (OCR): '{indicator}'.")
                        return True
                logger.info("Specific WhatsApp keywords not found via OCR.")
                        
            except ImportError:
                logger.info("pytesseract not available, skipping OCR text-based detection.")
            except Exception as e:
                logger.warning(f"OCR Text detection for WhatsApp failed: {e}")
            
            logger.warning("❌ WhatsApp not confidently detected on screen through available methods.")
            return False
            
        except Exception as e:
            logger.error(f"Error during visual checks for WhatsApp visibility: {e}")
            return False

    def open_whatsapp(self):
        """Open WhatsApp using subprocess and ensure it's visible before proceeding."""
        logger.info("Opening WhatsApp...")
        
        max_attempts = 3
        attempt = 1
        
        while attempt <= max_attempts:
            logger.info(f"Attempt {attempt} of {max_attempts} to open and verify WhatsApp...")
            
            try:
                # Detect operating system
                os_name = self.detect_os()
                
                # Try to open WhatsApp automatically
                logger.info("Attempting to open WhatsApp automatically...")
                
                if os_name == 'darwin':  # macOS
                    logger.info("Detected macOS - opening WhatsApp...")
                    
                    # Method 1: Try to open WhatsApp Desktop using subprocess
                    try:
                        logger.info("Trying to open WhatsApp Desktop app...")
                        result = subprocess.run(['open', '-a', 'WhatsApp'], 
                                              capture_output=True, text=True, timeout=10)
                        
                        if result.returncode == 0:
                            logger.info("✅ WhatsApp Desktop opened via subprocess")
                            time.sleep(3)  # Wait for app to load
                        else:
                            logger.warning(f"WhatsApp Desktop not found: {result.stderr}")
                            
                    except subprocess.TimeoutExpired:
                        logger.warning("WhatsApp Desktop opening timed out")
                    except Exception as e:
                        logger.warning(f"Failed to open WhatsApp Desktop: {e}")
                    
                    # Method 2: Try to open WhatsApp Web if desktop app didn't work
                    if not self.is_whatsapp_visible():
                        logger.info("Trying to open WhatsApp Web...")
                        
                        # Try to open in default browser
                        try:
                            result = subprocess.run(['open', 'https://web.whatsapp.com'], 
                                                  capture_output=True, text=True, timeout=10)
                            
                            if result.returncode == 0:
                                logger.info("✅ WhatsApp Web opened in default browser")
                                time.sleep(5)  # Wait for web page to load
                            else:
                                logger.warning(f"Failed to open WhatsApp Web: {result.stderr}")
                                
                        except Exception as e:
                            logger.warning(f"Failed to open WhatsApp Web: {e}")
                    
                    # Method 3: Try to open in specific browsers if still not visible
                    if not self.is_whatsapp_visible():
                        logger.info("Trying to open WhatsApp Web in specific browsers...")
                        
                        browsers = ['Safari', 'Google Chrome', 'Firefox', 'Microsoft Edge']
                        for browser in browsers:
                            try:
                                logger.info(f"Trying to open in {browser}...")
                                
                                # Use AppleScript to open WhatsApp Web in specific browser
                                applescript = f'''
                                tell application "{browser}"
                                    activate
                                    open location "https://web.whatsapp.com"
                                end tell
                                '''
                                
                                result = subprocess.run(['osascript', '-e', applescript], 
                                                      capture_output=True, text=True, timeout=10)
                                
                                if result.returncode == 0:
                                    logger.info(f"✅ WhatsApp Web opened in {browser}")
                                    time.sleep(5)  # Wait for web page to load
                                    break
                                else:
                                    logger.warning(f"Failed to open in {browser}: {result.stderr}")
                                    
                            except Exception as e:
                                logger.warning(f"Failed to open in {browser}: {e}")
                                continue
                    
                elif os_name == 'windows':  # Windows
                    logger.info("Detected Windows - opening WhatsApp...")
                    
                    # Method 1: Try WhatsApp protocol
                    try:
                        result = subprocess.run(['start', 'whatsapp://'], shell=True, 
                                              capture_output=True, text=True, timeout=10)
                        
                        if result.returncode == 0:
                            logger.info("✅ WhatsApp opened via protocol")
                            time.sleep(3)
                        else:
                            logger.warning(f"WhatsApp protocol failed: {result.stderr}")
                            
                    except Exception as e:
                        logger.warning(f"WhatsApp protocol opening failed: {e}")
                    
                    # Method 2: Try opening WhatsApp Web if desktop app didn't work
                    if not self.is_whatsapp_visible():
                        logger.info("Trying to open WhatsApp Web...")
                        try:
                            result = subprocess.run(['start', 'https://web.whatsapp.com'], shell=True,
                                                  capture_output=True, text=True, timeout=10)
                            
                            if result.returncode == 0:
                                logger.info("✅ WhatsApp Web opened")
                                time.sleep(5)
                            else:
                                logger.warning(f"WhatsApp Web opening failed: {result.stderr}")
                                
                        except Exception as e:
                            logger.warning(f"Failed to open WhatsApp Web: {e}")
                
                else:  # Linux and other systems
                    logger.warning(f"Detected {os_name} - trying generic method...")
                    
                    # Try to open WhatsApp Web in default browser
                    try:
                        result = subprocess.run(['xdg-open', 'https://web.whatsapp.com'], 
                                              capture_output=True, text=True, timeout=10)
                        
                        if result.returncode == 0:
                            logger.info("✅ WhatsApp Web opened")
                            time.sleep(5)
                        else:
                            logger.warning(f"Failed to open WhatsApp Web: {result.stderr}")
                            
                    except Exception as e:
                        logger.warning(f"Failed to open WhatsApp Web: {e}")
                
                # Try to maximize/focus the window using cross-platform methods
                try:
                    logger.info("Attempting to focus and maximize the window...")
                    time.sleep(2)  # Give window time to appear

                    if os_name == 'darwin':
                        # Try to bring WhatsApp to front and maximize using AppleScript
                        applescript = '''
                        tell application "WhatsApp"
                            activate
                        end tell

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
                            on error errMsg
                                log "Could not control WhatsApp. Error: " & errMsg
                            end try
                        end tell
                        '''
                        try:
                            subprocess.run(['osascript', '-e', applescript],
                                         capture_output=True, text=True, timeout=10)
                            logger.info("✅ macOS: Window focus and maximization command sent.")
                        except Exception as e_as:
                            logger.warning(f"macOS: AppleScript for maximization failed: {e_as}")

                    elif os_name == 'windows':
                        # Try to focus and maximize WhatsApp window
                        try:
                            whatsapp_windows = pyautogui.getWindowsWithTitle('WhatsApp')
                            if whatsapp_windows:
                                whatsapp_window = whatsapp_windows[0]
                                if not whatsapp_window.isMaximized:
                                    whatsapp_window.maximize()
                                whatsapp_window.activate()
                                logger.info("✅ Windows: WhatsApp window maximized and activated.")
                            else:
                                logger.warning("Windows: WhatsApp window not found by title, trying generic hotkey.")
                                pyautogui.hotkey('win', 'up')
                                logger.info("✅ Windows: Sent generic maximize command.")
                        except Exception as e_win:
                            logger.warning(f"Windows: Failed to maximize window: {e_win}, using hotkey fallback.")
                            pyautogui.hotkey('win', 'up')

                    else:  # Linux and other systems
                        try:
                            logger.info("Linux/Other: Sending generic maximize command.")
                            # Most Linux desktops use Win + Up to maximize.
                            pyautogui.hotkey('win', 'up')
                        except Exception as e_lin:
                            logger.warning(f"Linux/Other: Failed to send maximize hotkey: {e_lin}")

                except Exception as e:
                    logger.warning(f"Window management failed: {e}")
                
                time.sleep(2)
                
                # Check if WhatsApp is now visible
                if self.is_whatsapp_visible():
                    logger.info("✅ WhatsApp opened and is visible on screen!")
                    return
                else:
                    logger.warning(f"❌ WhatsApp automatic opening failed on attempt {attempt}")
                    
                    # If this was the last attempt, ask user to open manually
                    if attempt == max_attempts:
                        logger.warning("🔧 MANUAL INTERVENTION REQUIRED")
                        logger.warning("The bot could not automatically open WhatsApp.")
                        logger.warning("Please manually open WhatsApp on your system.")
                        logger.warning("")
                        
                        # Manual fallback loop
                        while True:
                            input("Press Enter after you have opened WhatsApp and it's visible on screen...")
                            
                            if self.is_whatsapp_visible():
                                logger.info("✅ WhatsApp is now visible! Continuing with the bot...")
                                return
                            else:
                                logger.warning("❌ WhatsApp is still not visible on screen.")
                                logger.warning("Please make sure WhatsApp is open and visible, then try again.")
                                
                                retry_choice = input("Type 'r' to retry detection, 'c' to continue anyway, or 'q' to quit: ").lower()
                                if retry_choice == 'c':
                                    logger.warning("⚠️  Continuing without WhatsApp verification...")
                                    logger.warning("The bot may fail when trying to send messages.")
                                    return
                                elif retry_choice == 'q':
                                    logger.info("Bot stopped by user.")
                                    raise KeyboardInterrupt("User chose to quit")
                                # If 'r' or any other input, continue the loop to retry
                    else:
                        logger.info(f"Retrying WhatsApp opening... (attempt {attempt + 1})")
                        attempt += 1
                        time.sleep(2)  # Wait before retry
                        continue
                        
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error(f"Error opening WhatsApp on attempt {attempt}: {e}")
                if attempt == max_attempts:
                    raise
                else:
                    attempt += 1
                    time.sleep(2)

    def navigate_and_send_message(self):
        """Navigate in WhatsApp and send the screenshots with messages."""
        logger.info("Navigating in WhatsApp...")
        
        try:
            # Click at coordinates (105, 105) - likely search or contact area
            logger.info("Clicking at coordinates (105, 105)")
            pyautogui.click(105, 105)
            time.sleep(1)
            
            # Type "AKQA Working Group"
            logger.info("Typing 'AKQA Working Group 1368'")
            pyautogui.write('AKQA Working Group 1368')
            time.sleep(1)
            
            # Click at coordinates (205, 205) - likely to select contact
            logger.info("Clicking at coordinates (205, 205)")
            pyautogui.click(205, 205)
            time.sleep(2)
            
            # Check for admin message
            if self.check_for_admin_message():
                # Check current time and if it's earlier than 9:30:00 AM, then calculate until 9:30:00 AM and sleep for that time
                current_time = datetime.now().strftime("%H:%M:%S")

                if current_time < "09:30:00":
                    time_until_930 = datetime.strptime("09:30:00", "%H:%M:%S") - datetime.strptime(current_time, "%H:%M:%S")
                    time_until_930_seconds = int(time_until_930.total_seconds())
                    # If time_until_930_seconds is greater than 9 hours and 30 minutes, then return
                    if time_until_930_seconds > 34200:
                        logger.info("Time until 9:30 AM is greater than 9 hours and 30 minutes, unable to send message.")
                        return
                    logger.info(f"Sleeping for {time_until_930_seconds} seconds until 9:30 AM ({time_until_900})")
                    time.sleep(time_until_930_seconds)
                    max_attempts = 10
                    attempt = 1
                    while attempt <= max_attempts:
                        logger.info(f"Attempt {attempt} of {max_attempts} to check for admin message...")
                        if not self.check_for_admin_message():
                            logger.info("Admin message not found, sending message.")
                            break
                        else:
                            logger.info("Admin message found, unable to send message.")
                            attempt += 1
                            time.sleep(2)
                    if attempt > max_attempts:
                        logger.info("Admin message found, unable to send message.")
                        return
                elif current_time > "20:00":
                    logger.info("Current time is later than 8PM, unable to send message.")
                    return
                else:
                    logger.info("Current time is between 9:30 AM and 8PM, attempting to send message.")
                    time.sleep(20) # Wait for 20 seconds to ensure admin message is not found

            # Click at coordinates (930, 930) - likely message input area
            logger.info("Clicking at coordinates (930, 930)")
            pyautogui.click(930, 930)
            time.sleep(1)
            
            # Variety of task completed message
            task_completed_message = [
                "Done with my tasks",
                "Finished my tasks today",
                "Tasks completed for today.",
                "all tasks completed today",
                "Done tasking for today"
            ]

            # Send tasks screenshot first
            logger.info("Sending tasks screenshot...")
            if hasattr(self, 'tasks_screenshot') and os.path.exists(self.tasks_screenshot):
                success = self.send_image_to_whatsapp(self.tasks_screenshot, random.choice(task_completed_message))
                if not success:
                    logger.warning("Failed to send tasks screenshot")
            
            logger.info("Message sent successfully")
            
        except Exception as e:
            logger.error(f"Error navigating and sending message: {e}")
            raise

    def check_for_admin_message(self):
        """
        Takes a screenshot of a specific region and checks for a target message.
        """
        import pytesseract
        try:
            # 1. Define the screen region to capture
            # The format is (left, top, width, height)
            x1, y1 = 445, 905
            x2, y2 = 1469, 955
            width = x2 - x1
            height = y2 - y1
            region_to_capture = (x1, y1, width, height)

            # The exact message we are looking for
            target_messages = ["Only admins can send messages", "Only admins can", "Only admins", "admin"]

            # 2. Take a screenshot of the specified region
            print(f"Capturing screen region: {region_to_capture}...")
            screenshot = pyautogui.screenshot(region=region_to_capture)

            # Convert PIL Image to OpenCV format
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # Optional preprocessing
            img = cv2.resize(img, None, fx=2, fy=2)  # Scale up for better OCR
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Optional: Save the screenshot to a file for debugging
            cv2.imwrite("debug_whatsapp_chatbox_screenshot.png", img)
            print("Debug screenshot saved as 'debug_whatsapp_chatbox_screenshot.png'")

            # 3. Use pytesseract to perform OCR and extract text
            extracted_text = pytesseract.image_to_string(screenshot, lang='eng')

            # Clean up the extracted text by removing leading/trailing whitespace
            cleaned_text = extracted_text.strip()
            print(f"Detected Text: '{cleaned_text}'")

            # 4. Check if the target message is in the extracted text
            # Using 'in' is more robust than '==' in case OCR picks up
            # extra characters or artifacts.
            if any(target_message in cleaned_text for target_message in target_messages):
                print(f"\n[SUCCESS] Found the message: '{target_messages}'")
                return True
            else:
                print(f"\n[INFO] The target message was not found.")
                return False

        except FileNotFoundError:
            print(
                "[ERROR] Tesseract not found. Please ensure it's installed and "
                "the path is configured correctly in the script."
            )
            return False
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False

    def check_balance_and_withdraw(self):
        """Checks balance, and if sufficient, attempts to make a withdrawal if one hasn't been made today."""
        logger.info("💰 Checking balance and withdrawal status...")
        
        try:
            # Step 0: Check if today is Saturday or Sunday. 
            today = datetime.now()
            if today.weekday() > 4:
                logger.info(f"Today is {today.strftime('%A')} (not within Monday to Friday). Skipping withdrawal.")
                return

            # Step 0.5: Check if today is 9:00 AM or above. If so, proceed, otherwise wait until 9:00 AM.
            current_time = datetime.now().strftime("%H:%M:%S")
            if current_time < "09:00:00":
                time_until_900 = datetime.strptime("09:00:00", "%H:%M:%S") - datetime.strptime(current_time, "%H:%M:%S")
                time_until_900_seconds = int(time_until_900.total_seconds())
                logger.info(f"Sleeping for {time_until_900_seconds} seconds until 9:00 AM ({time_until_900})")
                time.sleep(time_until_900_seconds)
            else:
                logger.info(f"Current time is {current_time}. Proceeding with withdrawal.")

            # Step 1: Navigate to Account page
            logger.info("Navigating to Account page to check balance...")
            self.driver.get("https://akqaflicksph.com/#/user")
            WebDriverWait(self.driver, 10).until(EC.url_contains("#/user"))
            time.sleep(3)

            # Step 2: Check personal balance
            balance_xpath = "//div//p[text()='Personal Balance(PHP)']/following-sibling::p"
            balance_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, balance_xpath))
            )
            balance_value = float(balance_element.text.strip())
            logger.info(f"Personal Balance: {balance_value} PHP")

            if balance_value < 60.0:
                logger.info("Balance is less than 60.0 PHP. Skipping withdrawal.")
                return

            # Step 3: Check for existing withdrawal today
            logger.info("Balance is sufficient. Checking for today's withdrawal records...")
            self.driver.get("https://akqaflicksph.com/#/user/wallet")
            WebDriverWait(self.driver, 10).until(EC.url_contains("#/user/wallet"))
            time.sleep(3)

            withdrawal_tab_xpath = "//div[contains(@class, 'van-tab')]//span[text()='Withdrawal Records']"
            withdrawal_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, withdrawal_tab_xpath))
            )
            withdrawal_tab.click()
            time.sleep(3)

            today_str = datetime.now().strftime('%d-%m-%Y')
            withdrawal_items_xpath = "//div[contains(@class, 'FundItem') and contains(@class, 'van-cell')]"

            try:
                withdrawal_items = self.driver.find_elements(By.XPATH, withdrawal_items_xpath)
                logger.info(f"Found {len(withdrawal_items)} withdrawal records.")
                
                for item in withdrawal_items:
                    try:
                        # More robust element finding
                        date_element = item.find_element(By.XPATH, ".//span[contains(text(), '-')]")
                        date_text = date_element.text.strip()
                        
                        if today_str in date_text:
                            amount_element = item.find_element(By.XPATH, ".//span[contains(@class, 'money-withdraw')]")
                            status_element = item.find_element(By.XPATH, ".//span[contains(@style, 'color: gray')]")
                            
                            amount_text = amount_element.text.strip()
                            status_text = status_element.text.strip()
                            
                            logger.info("✅ A withdrawal has already been made today.")
                            logger.info(f"   Date: {date_text}, Amount: {amount_text}, Status: {status_text}")
                            return
                    except NoSuchElementException:
                        continue  # Skip this item if elements not found
                        
                logger.info("No withdrawal found for today.")
                
            except Exception as e:
                logger.error(f"Error checking withdrawal records: {e}")
            
            logger.info("No withdrawal made today. Proceeding to withdraw 60 PHP...")
            self.driver.get("https://akqaflicksph.com/#/user/withdraw")
            WebDriverWait(self.driver, 10).until(EC.url_contains("#/user/withdraw"))
            time.sleep(3)

            amount_button_xpath = "//div[contains(@class, 'van-grid-item__content') and normalize-space(text()) = '60']"
            amount_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, amount_button_xpath)))
            amount_button.click()
            logger.info("Selected withdrawal amount: 60")
            time.sleep(1)

            password_input_xpath = "//input[@placeholder='Please enter the fund password']"
            password_input = self.driver.find_element(By.XPATH, password_input_xpath)
            password_input.send_keys(self.fund_password)
            logger.info("Entered fund password.")
            time.sleep(1)

            submit_button_xpath = "//button[contains(@class, 'van-button--danger') and .//span[text()='Submit']]"
            submit_button = self.driver.find_element(By.XPATH, submit_button_xpath)
            submit_button.click()
            logger.info("Submit button clicked.")
            time.sleep(3)

            logger.info("Verifying withdrawal by checking records again...")
            self.driver.get("https://akqaflicksph.com/#/user/wallet")
            WebDriverWait(self.driver, 10).until(EC.url_contains("#/user/wallet"))
            time.sleep(3)
            
            withdrawal_tab = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, withdrawal_tab_xpath)))
            withdrawal_tab.click()
            time.sleep(3)

            try:
                withdrawal_items = self.driver.find_elements(By.XPATH, withdrawal_items_xpath)
                logger.info(f"Found {len(withdrawal_items)} withdrawal records after submission.")
                
                found_pending_withdrawal = False
                
                for item in withdrawal_items:
                    try:
                        # Find date element
                        date_element = item.find_element(By.XPATH, ".//span[contains(text(), '-')]")
                        date_text = date_element.text.strip()
                        
                        if today_str in date_text:
                            try:
                                # Try to find status element
                                status_element = item.find_element(By.XPATH, ".//span[contains(@style, 'color: gray')]")
                                status_text = status_element.text.strip()
                                
                                # Also get amount for logging
                                amount_element = item.find_element(By.XPATH, ".//span[contains(@class, 'money-withdraw')]")
                                amount_text = amount_element.text.strip()
                                
                                logger.info(f"Today's withdrawal found: Date='{date_text}', Amount='{amount_text}', Status='{status_text}'")
                                
                                if "Pending Review" in status_text:
                                    logger.info("✅ Verification successful! New withdrawal is in Pending Review status.")
                                    found_pending_withdrawal = True
                                    break
                                else:
                                    logger.warning(f"⚠️  Today's withdrawal found but status is: '{status_text}' (expected: Pending Review)")
                                    found_pending_withdrawal = True  # Found today's withdrawal but different status
                                    break
                                    
                            except NoSuchElementException:
                                logger.warning(f"Found today's withdrawal but couldn't extract status information")
                                continue
                                
                    except NoSuchElementException:
                        continue  # Skip this item if date element not found
                
                if not found_pending_withdrawal:
                    logger.warning("⚠️  No withdrawal found for today after submission")
                    self.driver.save_screenshot("withdrawal_verification_failed.png")
                
            except Exception as e:
                logger.error(f"Error during withdrawal verification: {e}")
                self.driver.save_screenshot("withdrawal_verification_error.png")

        except Exception as e:
            logger.error(f"An error occurred during the balance and withdrawal process: {e}")
            self.driver.save_screenshot("withdrawal_process_error.png")

    def send_image_to_whatsapp(self, image_path, caption):
        """Send an image to WhatsApp with a caption using multiple methods."""
        try:
            os_name = self.detect_os()
            
            if os_name == 'darwin':  # macOS
                return self.send_image_macos(image_path, caption)
            elif os_name == 'windows':  # Windows
                return self.send_image_windows(image_path, caption)
            else:  # Linux and others
                return self.send_image_generic(image_path, caption)
                
        except Exception as e:
            logger.error(f"Error sending image {image_path}: {e}")
            return False

    def send_image_macos(self, image_path, caption):
        """Send image on macOS using AppleScript and drag-drop methods."""
        try:
            # Method 1: Use AppleScript to handle file attachment
            logger.info(f"Trying AppleScript method for {image_path}")
            
            # Get absolute path
            abs_path = os.path.abspath(image_path)
            
            # AppleScript to drag file to WhatsApp
            applescript = f'''
            tell application "System Events"
                -- First, make sure WhatsApp is frontmost
                set frontmost of process "WhatsApp" to true
                delay 0.5
                
                -- Get WhatsApp window
                tell process "WhatsApp"
                    -- Click in the message input area to ensure focus
                    click at {{930, 930}}
                    delay 0.5
                    
                    -- Use drag and drop
                    set theFile to POSIX file "{abs_path}"
                    
                    -- This will open the file in Preview/Finder, then we drag it
                    tell application "Finder"
                        open theFile
                        delay 1
                    end tell
                    
                    -- Now drag from Finder to WhatsApp
                    -- This is a simplified approach; we'll use a different method
                end tell
            end tell
            '''
            
            # Try a simpler AppleScript approach first
            try:
                # Method 1a: Use AppleScript to simulate drag and drop
                simple_script = f'''
                tell application "WhatsApp" to activate
                delay 1
                
                tell application "System Events"
                    tell process "WhatsApp"
                        -- Try to find attachment button or use drag drop
                        try
                            -- Simulate drag and drop by opening file first
                            do shell script "open '{abs_path}'"
                            delay 2
                            
                            -- Then use copy/paste from the opened image
                            tell application "System Events" to keystroke "a" using command down
                            delay 0.5
                            tell application "System Events" to keystroke "c" using command down
                            delay 0.5
                            
                            -- Switch back to WhatsApp and paste
                            tell application "WhatsApp" to activate
                            delay 0.5
                            click at {{930, 930}} 
                            delay 0.5
                            tell application "System Events" to keystroke "v" using command down
                            delay 2 
                        end try
                    end tell
                end tell
                '''
                
                result = subprocess.run(['osascript', '-e', simple_script], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    logger.info("✅ AppleScript method successful (image pasted/preview shown)")
                    time.sleep(2) # Allow preview to fully load and caption field to be active
                    
                    # Clear existing text in caption field and add new caption
                    logger.info("Clearing caption field and typing new caption...")
                    time.sleep(0.5) # Ensure focus on caption field in preview
                    pyautogui.hotkey('command', 'a') # Select all
                    time.sleep(0.2)
                    pyautogui.press('backspace') # Clear selection
                    time.sleep(0.5) # Crucial pause before typing caption
                    
                    pyautogui.write(caption)
                    time.sleep(1)
                    pyautogui.press('enter') # Send image with caption
                    time.sleep(2)
                    
                    return True
                else:
                    logger.warning(f"AppleScript method failed: {result.stderr}")
                    
            except Exception as e:
                logger.warning(f"AppleScript method failed: {e}")
            
            # Method 2: Use attachment button approach
            logger.info("Trying attachment button method...")
            
            try:
                # Click attachment button (paperclip icon) - coordinates may need adjustment
                attachment_coords = [(890, 930), (900, 930), (910, 930), (850, 930)]
                
                for coord in attachment_coords:
                    try:
                        pyautogui.click(coord[0], coord[1])
                        time.sleep(1)
                        
                        # Look for "Photos & Videos" or similar option
                        # This varies by WhatsApp version, try different approaches
                        
                        # Try clicking on photos option
                        pyautogui.click(950, 850)  # Approximate location of photos option
                        time.sleep(2)
                        
                        # Navigate to the file using Finder dialog
                        # Press Cmd+Shift+G to go to folder
                        pyautogui.hotkey('cmd', 'shift', 'g')
                        time.sleep(1)
                        
                        # Type the directory path
                        dir_path = os.path.dirname(abs_path)
                        pyautogui.write(dir_path)
                        pyautogui.press('enter')
                        time.sleep(2)
                        
                        # Type the filename
                        filename = os.path.basename(abs_path)
                        pyautogui.write(filename)
                        time.sleep(1)
                        
                        pyautogui.press('enter') # Select file
                        time.sleep(2) # Wait for preview to appear
                        
                        # Clear existing text in caption field and add new caption
                        logger.info("Clearing caption field and typing new caption...")
                        time.sleep(0.5) # Ensure focus on caption field in preview
                        pyautogui.hotkey('command', 'a') # Select all
                        time.sleep(0.2)
                        pyautogui.press('backspace') # Clear selection
                        time.sleep(0.5) # Crucial pause before typing caption
                        
                        pyautogui.write(caption)
                        time.sleep(1)
                        
                        pyautogui.press('enter') # Send the image
                        time.sleep(3)
                        
                        logger.info("✅ Attachment button method successful")
                        return True
                        
                    except Exception as e:
                        logger.warning(f"Attachment method with coord {coord} failed: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Attachment button method failed: {e}")
            
            # Method 3: Manual fallback with user guidance
            logger.warning("Automatic image sending failed, using manual fallback...")
            
            # Open the image file for user to see
            subprocess.run(['open', abs_path], capture_output=True)
            
            print(f"\n📷 MANUAL IMAGE UPLOAD REQUIRED")
            print(f"   Image opened: {os.path.basename(image_path)}")
            print(f"   Please manually:")
            print(f"   1. Drag the opened image to WhatsApp")
            print(f"   2. Add caption: {caption}")
            print(f"   3. Send the image")
            
            input("   Press Enter when you've sent the image...")
            
            return True
            
        except Exception as e:
            logger.error(f"All macOS image sending methods failed: {e}")
            return False

    def send_image_windows(self, image_path, caption):
        """Send image on Windows using clipboard and file explorer."""
        try:
            # Method 1: Copy image to clipboard and paste
            logger.info("Trying clipboard method for Windows...")
            
            # Open image and copy to clipboard
            from PIL import Image
            img = Image.open(image_path)
            
            output = io.BytesIO()
            img.convert("RGB").save(output, format='BMP') # Using BMP for broader clipboard compatibility
            data = output.getvalue()[14:] # The BMP header needs to be stripped for CF_DIB
            output.close()
            
            try:
                import win32clipboard
                
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
                
                pyautogui.click(930, 930) # Click main chat input
                time.sleep(1)
                pyautogui.hotkey('ctrl', 'v') # Paste image
                time.sleep(2) # Wait for image preview to appear
                
                # Clear existing text in caption field and add new caption
                logger.info("Clearing caption field and typing new caption...")
                time.sleep(0.5) # Ensure focus on caption field in preview
                pyautogui.hotkey('ctrl', 'a') # Select all
                time.sleep(0.2)
                pyautogui.press('backspace') # Clear selection
                time.sleep(0.5) # Crucial pause before typing caption
                
                pyautogui.write(caption)
                time.sleep(1)
                pyautogui.press('enter') # Send image with caption
                time.sleep(2)
                
                logger.info("✅ Windows clipboard method successful")
                return True
                
            except ImportError:
                logger.warning("win32clipboard not available, trying attachment method...")
            except Exception as e_clip: # Catch specific clipboard errors
                logger.warning(f"Windows clipboard method failed: {e_clip}")


            # Method 2: Use attachment button
            logger.info("Trying attachment button method for Windows...")
            
            pyautogui.click(900, 930) # Attachment button
            time.sleep(1)
            
            pyautogui.click(950, 850) # Photos option (adjust if necessary)
            time.sleep(2)
            
            pyautogui.write(os.path.abspath(image_path))
            pyautogui.press('enter') # Select file
            time.sleep(2) # Wait for image preview to appear
            
            # Clear existing text in caption field and add new caption
            logger.info("Clearing caption field and typing new caption...")
            time.sleep(0.5) # Ensure focus on caption field in preview
            pyautogui.hotkey('ctrl', 'a') # Select all
            time.sleep(0.2)
            pyautogui.press('backspace') # Clear selection
            time.sleep(0.5) # Crucial pause before typing caption
            
            pyautogui.write(caption)
            time.sleep(1)
            pyautogui.press('enter') # Send image with caption
            time.sleep(2)
            
            logger.info("✅ Windows attachment method successful")
            return True
            
        except Exception as e:
            logger.error(f"Windows image sending failed: {e}")
            return False

    def send_image_generic(self, image_path, caption):
        """Generic image sending method for other platforms (assumed Linux-like)."""
        try:
            logger.info("Using generic image sending method (assuming Linux-like)...")
            
            pyautogui.click(900, 930)  # Attachment button
            time.sleep(1)
            pyautogui.click(950, 850)  # Photos option
            time.sleep(2)
            
            pyautogui.write(os.path.abspath(image_path))
            pyautogui.press('enter') # Select file
            time.sleep(2) # Wait for image preview to appear
            
            # Clear existing text in caption field and add new caption
            logger.info("Clearing caption field and typing new caption...")
            time.sleep(0.5) # Ensure focus on caption field in preview
            pyautogui.hotkey('ctrl', 'a') # Select all (Ctrl+A for Linux)
            time.sleep(0.2)
            pyautogui.press('backspace') # Clear selection
            time.sleep(0.5) # Crucial pause before typing caption
            
            pyautogui.write(caption)
            time.sleep(1)
            pyautogui.press('enter') # Send image with caption
            time.sleep(2)
            
            logger.info("✅ Generic method successful")
            return True
            
        except Exception as e:
            logger.error(f"Generic image sending failed: {e}")
            return False

    def close_whatsapp(self):
        """Close WhatsApp application."""
        logger.info("Closing WhatsApp...")
        
        try:
            # Detect OS and use appropriate close command
            os_name = self.detect_os()
            if os_name == 'darwin':  # macOS
                pyautogui.hotkey('cmd', 'q')  # Quit application on macOS
            else:  # Windows/Linux
                pyautogui.hotkey('alt', 'f4')  # Alt+F4 to close on Windows
            
            time.sleep(1)
            logger.info("WhatsApp closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing WhatsApp: {e}")
            # Continue anyway, as this is not critical
    
    def cleanup(self):
        """Clean up resources and temporary files."""
        logger.info("Cleaning up...")
        
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def complete_tasks_via_api(self) -> bool:
        """Complete tasks using the API method, then open browser for screenshot."""
        logger.info("Using API method to complete tasks...")
        session = requests.Session()
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://akqaflicksph.com',
            'referer': 'https://akqaflicksph.com/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        }
        # 1. Login
        login_data = {
            'username': self.username,
            'password': self.password,
            'language': 'fil_ph',
            'referer': 'https://akqaflicksph.com/#/login',
        }
        login_resp = session.post('https://api.aksystemph.com/api/User/login', headers=headers, data=login_data)
        if login_resp.status_code != 200:
            logger.error(f"Login API failed: {login_resp.status_code}")
            raise Exception("API login failed")
        login_json = login_resp.json()
        if login_json.get('code') != 1:
            logger.error(f"Login API error: {login_json}")
            raise Exception("API login error")
        token = login_json['data']['token']
        useridentity = login_json['data']['useridentity']
        self.identity = useridentity
        level = login_json['data']['level']
        task_num = login_json['data']['task_num']
        logger.info(f"API login success. Identity: {useridentity}, Level: {level}")
        # 2. Loop: fetch task list, process first available, until none left
        while True:
            task_list_data = {
                'id': str(task_num),
                'task_level': str(level),
                'page_no': '1',
                'language': 'fil_ph',
                'referer': f'https://akqaflicksph.com/#/taskList/{task_num}/{level}',
                'token': token,
            }
            task_list_resp = session.post('https://api.aksystemph.com/api/Task/getTaskList', headers=headers, data=task_list_data)
            if task_list_resp.status_code != 200:
                logger.error(f"getTaskList API failed: {task_list_resp.status_code}")
                return False
            task_list_json = task_list_resp.json()
            if task_list_json.get('code') != 1:
                logger.error(f"getTaskList API error: {task_list_json}")
                return False
            taskNumArr = task_list_json['data']['taskNumArr']
            tasks_remaining = taskNumArr[0] if taskNumArr else 0
            logger.info(f"Tasks remaining: {tasks_remaining}")
            task_list = task_list_json['data']['list']
            if not task_list or tasks_remaining == 0:
                logger.info("No tasks available to process via API.")
                break
            # Always process the first available task
            task = task_list[0]
            task_id = task['id']
            logger.info(f"Processing task {task_id} via API...")
            receive_data = {
                'id': str(task_id),
                'language': 'fil_ph',
                'referer': f'https://akqaflicksph.com/#/taskList/{task_num}/{level}',
                'token': token,
            }
            receive_resp = session.post('https://api.aksystemph.com/api/Task/receiveTask', headers=headers, data=receive_data)
            if receive_resp.status_code != 200 or receive_resp.json().get('code') != 1:
                logger.warning(f"Failed to receive task {task_id}: {receive_resp.text}")
                # Try to fetch taskOrderList for in-progress task
                logger.info("Checking for in-progress task via taskOrderList API...")
                task_order_data = {
                    'status': '1',
                    'page_no': '1',
                    'language': 'en_us',
                    'referer': 'https://akqaflicksph.com/#/myTask',
                    'token': token,
                }
                task_order_resp = session.post('https://api.aksystemph.com/api/Task/taskOrderList', headers=headers, data=task_order_data)
                if task_order_resp.status_code == 200 and task_order_resp.json().get('code') == 1:
                    lists = task_order_resp.json()['data'].get('lists', [])
                    if lists:
                        in_progress_task_id = lists[0]['task_id']
                        logger.info(f"Found in-progress task: {in_progress_task_id}, submitting it via API...")
                        submit_data = {
                            'id': str(in_progress_task_id),
                            'seconds': '11',
                            'language': 'fil_ph',
                            'referer': f'https://akqaflicksph.com/#/task/video/{in_progress_task_id}',
                            'token': token,
                        }
                        submit_resp = session.post('https://api.aksystemph.com/api/Task/submitTask', headers=headers, data=submit_data)
                        if submit_resp.status_code == 200 and submit_resp.json().get('code') == 1:
                            logger.info(f"In-progress task {in_progress_task_id} submitted successfully.")
                            time.sleep(10)
                            continue
                        else:
                            logger.warning(f"Failed to submit in-progress task {in_progress_task_id}: {submit_resp.text}")
                continue
            logger.info(f"Submitting task {task_id} via API...")
            submit_data = {
                'id': str(task_id),
                'seconds': '11',
                'language': 'fil_ph',
                'referer': f'https://akqaflicksph.com/#/task/video/{task_id}',
                'token': token,
            }
            submit_resp = session.post('https://api.aksystemph.com/api/Task/submitTask', headers=headers, data=submit_data)
            if submit_resp.status_code != 200 or submit_resp.json().get('code') != 1:
                logger.warning(f"Failed to submit task {task_id}: {submit_resp.text}")
                continue
            logger.info(f"Task {task_id} submitted successfully.")
            time.sleep(10)
        logger.info("API method: Task completion step complete.")
        return True

    def run(self):
        """Run the complete automation workflow."""

        method = self.complete_tasks_via_api if self.default_method == 'api' else self.start_tasks
        
        logger.info("Starting Ad Watcher Bot...")
        try:
            # Step 1: Login to website
            self.login_to_website()
            # Step 2: Setup task prerequisites
            self.setup_task_prerequisites()
            # Step 3: Start tasks
            if method() or self.complete_all_steps:
                # Step 4: Withdraw if applicable
                self.check_balance_and_withdraw()
                # Step 5: Wait and take screenshot
                self.wait_and_screenshot()
                # Step 6: Open WhatsApp
                self.open_whatsapp()
                # Step 7: Navigate and send message
                self.navigate_and_send_message()
                # Step 8: Close WhatsApp
                self.close_whatsapp()
            # Step 9: Check balance and withdraw if applicable
            self.check_balance_and_withdraw()
            logger.info("Ad Watcher Bot completed successfully!")
        except Exception as e:
            logger.error(f"Bot execution failed: {e}")
            raise
        finally:
            self.cleanup()

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Ad Watcher Bot")
    parser.add_argument('-c', '--complete', action='store_true', help='Complete all steps even if no tasks were done')
    parser.add_argument('--api', action='store_true', help='Only complete tasks via API and exit')
    args = parser.parse_args()
    
    bot = None  # Initialize bot to None
    try:
        bot = AdWatcherBot(complete_all_steps=args.complete)
        if args.api:
            logger.info("API-only mode selected. Completing tasks via API...")
            tasks_completed = bot.complete_tasks_via_api()
            if tasks_completed:
                logger.info("API tasks completed successfully.")
            else:
                logger.warning("Could not complete tasks via API.")
        else:
            bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        if bot and not args.api:  # Only run cleanup if it's not in API-only mode
            bot.cleanup()
    return 0

if __name__ == "__main__":
    exit(main()) 