#!/usr/bin/env python3
"""
Simple Website Inspector
A basic tool to inspect akqaflicksph.com and find login elements.
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def main():
    print("🔍 Simple AKQA Website Inspector")
    print("=" * 40)
    
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Browser opened")
        
        print("📡 Loading https://akqaflicksph.com...")
        driver.get("https://akqaflicksph.com")
        time.sleep(5)  # Wait for page to load
        
        # Basic info
        print(f"📄 Title: {driver.title}")
        print(f"🔗 URL: {driver.current_url}")
        
        # Take screenshot first
        driver.save_screenshot("simple_inspection.png")
        print("📸 Screenshot saved: simple_inspection.png")
        
        # Count elements
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        all_links = driver.find_elements(By.TAG_NAME, "a")
        
        print(f"\n📊 Element counts:")
        print(f"   Input fields: {len(all_inputs)}")
        print(f"   Buttons: {len(all_buttons)}")
        print(f"   Links: {len(all_links)}")
        
        # Look for text that might indicate login
        page_text = driver.page_source.lower()
        login_keywords = ['login', 'sign in', 'username', 'password', 'email']
        
        print(f"\n🔍 Login-related keywords found:")
        for keyword in login_keywords:
            if keyword in page_text:
                print(f"   ✅ '{keyword}' found in page")
            else:
                print(f"   ❌ '{keyword}' not found")
        
        # Check for specific elements that might be login-related
        potential_selectors = [
            ("Username input", "input[type='text']"),
            ("Email input", "input[type='email']"),
            ("Password input", "input[type='password']"),
            ("Login button", "button"),
            ("Submit input", "input[type='submit']"),
        ]
        
        print(f"\n🎯 Checking potential login elements:")
        for desc, selector in potential_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"   ✅ {desc}: {len(elements)} found")
                    # Show first element details
                    elem = elements[0]
                    attrs = []
                    for attr in ['id', 'name', 'class', 'placeholder']:
                        value = elem.get_attribute(attr)
                        if value:
                            attrs.append(f"{attr}='{value}'")
                    if attrs:
                        print(f"      First element: {' '.join(attrs)}")
                else:
                    print(f"   ❌ {desc}: none found")
            except Exception as e:
                print(f"   ⚠️ {desc}: error - {e}")
        
        print("\n⏳ Keeping browser open for 15 seconds for manual inspection...")
        print("   Look at the browser window to see the actual website")
        time.sleep(15)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()
            print("🔒 Browser closed")

if __name__ == "__main__":
    main() 