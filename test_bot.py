#!/usr/bin/env python3
"""
Test Bot Components
This script allows you to test individual parts of the Ad Watcher Bot
to help debug issues and verify functionality.
"""

import os
import sys
import time
from main import AdWatcherBot

def test_environment():
    """Test if environment variables are properly configured."""
    print("🔧 Testing Environment Configuration...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        username = os.getenv('WEBSITE_USERNAME')
        password = os.getenv('WEBSITE_PASSWORD')
        
        if not username or not password:
            print("❌ Environment variables not found")
            print("   Make sure .env file exists with WEBSITE_USERNAME and WEBSITE_PASSWORD")
            return False
        
        if username == "your_username_here" or password == "your_password_here":
            print("❌ Environment variables not configured")
            print("   Please update .env file with your actual credentials")
            return False
        
        print("✅ Environment variables configured")
        print(f"   Username: {username[:3]}***")
        print(f"   Password: ***")
        return True
        
    except Exception as e:
        print(f"❌ Error testing environment: {e}")
        return False

def test_selenium():
    """Test if Selenium and ChromeDriver are working."""
    print("\n🌐 Testing Selenium WebDriver...")
    try:
        bot = AdWatcherBot()
        print("✅ WebDriver initialized successfully")
        
        # Test basic navigation
        bot.driver.get("https://www.google.com")
        time.sleep(2)
        
        title = bot.driver.title
        print(f"✅ Navigation test successful (Title: {title})")
        
        bot.driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Selenium test failed: {e}")
        print("   Make sure ChromeDriver is installed and in PATH")
        return False

def test_pyautogui():
    """Test if PyAutoGUI is working."""
    print("\n🖱️  Testing PyAutoGUI...")
    try:
        import pyautogui
        
        # Test screen size detection
        size = pyautogui.size()
        print(f"✅ Screen size detected: {size}")
        
        # Test mouse position
        pos = pyautogui.position()
        print(f"✅ Mouse position: {pos}")
        
        # Test screenshot
        screenshot = pyautogui.screenshot()
        print(f"✅ Screenshot taken: {screenshot.size}")
        
        return True
        
    except Exception as e:
        print(f"❌ PyAutoGUI test failed: {e}")
        return False

def test_website_login():
    """Test login to the target website."""
    print("\n🔐 Testing Website Login...")
    try:
        bot = AdWatcherBot()
        
        print("   Navigating to aqkaflicksph.com...")
        bot.login_to_website()
        
        print("✅ Login test completed")
        print("   Check browser window to verify login success")
        
        input("   Press Enter to continue (check if login was successful)...")
        
        bot.driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Website login test failed: {e}")
        return False

def test_internship_button():
    """Test finding and clicking the Internship button."""
    print("\n🎯 Testing Internship Button Detection...")
    try:
        bot = AdWatcherBot()
        
        # First login
        print("   Logging in...")
        bot.login_to_website()
        
        print("   Looking for Internship button...")
        bot.click_internship_button()
        
        print("✅ Internship button test completed")
        print("   Check browser window to verify button was clicked")
        
        input("   Press Enter to continue...")
        
        bot.driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Internship button test failed: {e}")
        return False

def test_screenshot():
    """Test screenshot functionality."""
    print("\n📸 Testing Screenshot...")
    try:
        import pyautogui
        
        print("   Taking screenshot...")
        screenshot = pyautogui.screenshot()
        
        print("   Saving screenshot...")
        screenshot.save('test_screenshot.png')
        
        print("✅ Screenshot test completed")
        print("   Check test_screenshot.png in project directory")
        
        return True
        
    except Exception as e:
        print(f"❌ Screenshot test failed: {e}")
        return False

def test_whatsapp():
    """Test WhatsApp opening."""
    print("\n💬 Testing WhatsApp...")
    print("   This will attempt to open WhatsApp...")
    print("   WARNING: This will actually open WhatsApp on your system!")
    
    response = input("   Continue? (y/N): ").lower()
    if response != 'y':
        print("   Skipped WhatsApp test")
        return True
    
    try:
        bot = AdWatcherBot()
        bot.open_whatsapp()
        
        print("✅ WhatsApp test completed")
        print("   Check if WhatsApp opened successfully")
        
        input("   Press Enter to continue...")
        return True
        
    except Exception as e:
        print(f"❌ WhatsApp test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Ad Watcher Bot Component Tester")
    print("=" * 50)
    print("This script will test individual components of the bot.")
    print("Choose which tests to run:")
    print()
    
    tests = [
        ("Environment Configuration", test_environment),
        ("Selenium WebDriver", test_selenium),
        ("PyAutoGUI", test_pyautogui),
        ("Website Login", test_website_login),
        ("Internship Button", test_internship_button),
        ("Screenshot", test_screenshot),
        ("WhatsApp Opening", test_whatsapp),
    ]
    
    while True:
        print("\nAvailable tests:")
        for i, (name, _) in enumerate(tests, 1):
            print(f"  {i}. {name}")
        print(f"  {len(tests) + 1}. Run all tests")
        print("  0. Exit")
        
        try:
            choice = input("\nEnter your choice: ").strip()
            
            if choice == "0":
                print("Goodbye! 👋")
                break
            elif choice == str(len(tests) + 1):
                # Run all tests
                print("\n🚀 Running all tests...")
                results = []
                for name, test_func in tests:
                    print(f"\n{'='*20} {name} {'='*20}")
                    result = test_func()
                    results.append((name, result))
                
                print("\n" + "="*50)
                print("📊 Test Results Summary:")
                for name, result in results:
                    status = "✅ PASS" if result else "❌ FAIL"
                    print(f"   {status} - {name}")
                
                passed = sum(1 for _, result in results if result)
                total = len(results)
                print(f"\n🎯 Tests passed: {passed}/{total}")
                
            elif choice.isdigit() and 1 <= int(choice) <= len(tests):
                test_index = int(choice) - 1
                name, test_func = tests[test_index]
                print(f"\n{'='*20} {name} {'='*20}")
                result = test_func()
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"\n{status} - {name}")
            else:
                print("Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user. Goodbye! 👋")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main() 