#!/usr/bin/env python3
"""
Password Field Debugger - Deep analysis of the Vant UI password field
to understand why it's not interactable.
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PasswordFieldDebugger:
    def __init__(self):
        load_dotenv()
        self.setup_selenium()
    
    def setup_selenium(self):
        """Set up Selenium WebDriver."""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def navigate_and_open_login(self):
        """Navigate to website and open login modal."""
        logger.info("Navigating to akqaflicksph.com and opening login...")
        
        self.driver.get("https://akqaflicksph.com")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)
        
        # Click button to reveal login form
        try:
            dialog_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".van-button"))
            )
            dialog_button.click()
            time.sleep(2)
            logger.info("Login modal opened")
        except Exception as e:
            logger.warning(f"Could not open login modal: {e}")
    
    def analyze_password_field(self):
        """Comprehensive analysis of the password field."""
        logger.info("=== PASSWORD FIELD ANALYSIS ===")
        
        try:
            # Find the password field
            password_field = self.driver.find_element(By.CSS_SELECTOR, ".van-field__control")
            logger.info("✅ Password field found!")
            
            # 1. Basic properties
            logger.info("\n--- BASIC PROPERTIES ---")
            logger.info(f"Tag name: {password_field.tag_name}")
            logger.info(f"Type: {password_field.get_attribute('type')}")
            logger.info(f"Class: {password_field.get_attribute('class')}")
            logger.info(f"Placeholder: {password_field.get_attribute('placeholder')}")
            logger.info(f"Autocomplete: {password_field.get_attribute('autocomplete')}")
            logger.info(f"Name: {password_field.get_attribute('name')}")
            logger.info(f"ID: {password_field.get_attribute('id')}")
            logger.info(f"Value: '{password_field.get_attribute('value')}'")
            
            # 2. Interactability checks
            logger.info("\n--- INTERACTABILITY CHECKS ---")
            logger.info(f"Is displayed: {password_field.is_displayed()}")
            logger.info(f"Is enabled: {password_field.is_enabled()}")
            logger.info(f"Is selected: {password_field.is_selected()}")
            
            # 3. CSS properties
            logger.info("\n--- CSS PROPERTIES ---")
            css_props = ['visibility', 'display', 'opacity', 'pointer-events', 'z-index', 'position']
            for prop in css_props:
                value = self.driver.execute_script(f"return getComputedStyle(arguments[0]).{prop};", password_field)
                logger.info(f"{prop}: {value}")
            
            # 4. DOM attributes
            logger.info("\n--- ALL DOM ATTRIBUTES ---")
            attrs = self.driver.execute_script("""
                var attrs = {};
                for (var i = 0; i < arguments[0].attributes.length; i++) {
                    var attr = arguments[0].attributes[i];
                    attrs[attr.name] = attr.value;
                }
                return attrs;
            """, password_field)
            for attr, value in attrs.items():
                logger.info(f"{attr}: {value}")
            
            # 5. Parent container analysis
            logger.info("\n--- PARENT CONTAINER ANALYSIS ---")
            parent = password_field.find_element(By.XPATH, "..")
            logger.info(f"Parent tag: {parent.tag_name}")
            logger.info(f"Parent class: {parent.get_attribute('class')}")
            logger.info(f"Parent style: {parent.get_attribute('style')}")
            
            # 6. Overlapping elements check
            logger.info("\n--- OVERLAPPING ELEMENTS CHECK ---")
            location = password_field.location
            size = password_field.size
            center_x = location['x'] + size['width'] // 2
            center_y = location['y'] + size['height'] // 2
            
            element_at_point = self.driver.execute_script(
                f"return document.elementFromPoint({center_x}, {center_y});"
            )
            
            if element_at_point:
                logger.info(f"Element at center point: {element_at_point.tag_name}")
                logger.info(f"Element class: {element_at_point.get_attribute('class')}")
                logger.info(f"Same element? {element_at_point == password_field}")
            
            # 7. Event listeners check
            logger.info("\n--- EVENT LISTENERS CHECK ---")
            has_listeners = self.driver.execute_script("""
                var element = arguments[0];
                var events = [];
                
                // Check for common events
                var eventTypes = ['click', 'focus', 'blur', 'input', 'change', 'keydown', 'keyup'];
                eventTypes.forEach(function(type) {
                    if (element['on' + type] !== null) {
                        events.push(type + ' (inline)');
                    }
                });
                
                return events;
            """, password_field)
            logger.info(f"Event listeners: {has_listeners}")
            
            # 8. Vue.js/Framework detection
            logger.info("\n--- VUE.JS / FRAMEWORK DETECTION ---")
            vue_info = self.driver.execute_script("""
                var element = arguments[0];
                var info = {};
                
                info.hasVue = !!element.__vue__;
                info.hasVNode = !!element._vnode;
                info.hasReact = !!element._reactInternalFiber || !!element._reactInternalInstance;
                
                if (element.__vue__) {
                    info.vueComponentName = element.__vue__.$options.name || 'unknown';
                }
                
                info.windowVue = !!window.Vue;
                info.windowReact = !!window.React;
                
                return info;
            """, password_field)
            for key, value in vue_info.items():
                logger.info(f"{key}: {value}")
            
            # 9. Readonly/disabled checks
            logger.info("\n--- FIELD STATE CHECKS ---")
            field_state = self.driver.execute_script("""
                var element = arguments[0];
                return {
                    readonly: element.readOnly,
                    disabled: element.disabled,
                    required: element.required,
                    maxLength: element.maxLength,
                    minLength: element.minLength
                };
            """, password_field)
            for key, value in field_state.items():
                logger.info(f"{key}: {value}")
            
            # 10. Try different interaction methods
            logger.info("\n--- INTERACTION TESTS ---")
            
            # Test 1: Try clicking
            try:
                password_field.click()
                logger.info("✅ Click successful")
            except Exception as e:
                logger.error(f"❌ Click failed: {e}")
            
            # Test 2: Try ActionChains click
            try:
                ActionChains(self.driver).click(password_field).perform()
                logger.info("✅ ActionChains click successful")
            except Exception as e:
                logger.error(f"❌ ActionChains click failed: {e}")
            
            # Test 3: Try JavaScript click
            try:
                self.driver.execute_script("arguments[0].click();", password_field)
                logger.info("✅ JavaScript click successful")
            except Exception as e:
                logger.error(f"❌ JavaScript click failed: {e}")
            
            # Test 4: Try focus
            try:
                password_field.send_keys("")  # Empty send_keys to focus
                logger.info("✅ Focus successful")
            except Exception as e:
                logger.error(f"❌ Focus failed: {e}")
            
            # Test 5: Try JavaScript focus
            try:
                self.driver.execute_script("arguments[0].focus();", password_field)
                logger.info("✅ JavaScript focus successful")
            except Exception as e:
                logger.error(f"❌ JavaScript focus failed: {e}")
            
            # Test 6: Try sending a single character
            try:
                password_field.send_keys("a")
                current_value = password_field.get_attribute("value")
                logger.info(f"✅ Single character input successful. Value: '{current_value}'")
            except Exception as e:
                logger.error(f"❌ Single character input failed: {e}")
            
            # 11. Check for form validation or special handling
            logger.info("\n--- FORM VALIDATION CHECK ---")
            form_element = password_field.find_element(By.XPATH, ".//ancestor::form[1]")
            if form_element:
                logger.info(f"Form found: {form_element.tag_name}")
                logger.info(f"Form class: {form_element.get_attribute('class')}")
                logger.info(f"Form action: {form_element.get_attribute('action')}")
                logger.info(f"Form method: {form_element.get_attribute('method')}")
            else:
                logger.info("No form element found")
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
        
        # Take a screenshot for visual inspection
        self.driver.save_screenshot("password_field_debug_analysis.png")
        logger.info("Debug screenshot saved as: password_field_debug_analysis.png")
    
    def try_alternative_selectors(self):
        """Try to find the password field using different selectors."""
        logger.info("\n=== ALTERNATIVE SELECTOR TESTING ===")
        
        selectors = [
            "input[type='password']",
            "input[placeholder*='Password']",
            "input[placeholder*='password']",
            ".van-field__control",
            ".van-field input",
            "input[placeholder='Ilagay ang Password sa Pag-login']",
            "input[autocomplete='off']",
            "[data-v-*] input[type='password']"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                logger.info(f"Selector '{selector}': Found {len(elements)} elements")
                
                for i, elem in enumerate(elements):
                    placeholder = elem.get_attribute('placeholder') or 'no-placeholder'
                    class_name = elem.get_attribute('class') or 'no-class'
                    visible = elem.is_displayed()
                    logger.info(f"  Element {i+1}: placeholder='{placeholder}', class='{class_name}', visible={visible}")
                    
            except Exception as e:
                logger.error(f"Selector '{selector}' failed: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'driver'):
            self.driver.quit()

def main():
    debugger = PasswordFieldDebugger()
    
    try:
        debugger.navigate_and_open_login()
        debugger.analyze_password_field()
        debugger.try_alternative_selectors()
        
        # Keep browser open for manual inspection
        input("\nPress Enter to close browser and exit...")
        
    except Exception as e:
        logger.error(f"Debugging failed: {e}")
    finally:
        debugger.cleanup()

if __name__ == "__main__":
    main() 