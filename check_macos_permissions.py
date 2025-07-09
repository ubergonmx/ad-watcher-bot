#!/usr/bin/env python3
"""
macOS Permission Checker for Ad Watcher Bot
This utility checks if the required macOS permissions are granted for the bot to function.
Run this before running the main bot to verify your setup.
"""

import platform
import pyautogui
import logging
import time
import subprocess
import os
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_screenshot_permission():
    """Check if Screen Recording permission is granted."""
    try:
        logger.info("Testing Screen Recording permission...")
        logger.info("NOTE: This is only needed for WhatsApp detection, not for main bot screenshots")
        
        # Try to take a small screenshot 
        test_screenshot = pyautogui.screenshot(region=(0, 0, 100, 100))

        # Save the screenshot to a file for manual verification
        test_screenshot.save('test_screenshot.png')
        logger.info(f"Screenshot saved as: test_screenshot.png for manual verification")    
        
        # Check if screenshot actually contains data
        if test_screenshot and test_screenshot.size[0] > 0 and test_screenshot.size[1] > 0:
            # Get the actual pixel data
            pixels = list(test_screenshot.getdata())
            
            # More sophisticated check for empty/black screenshots
            if len(pixels) == 0:
                logger.warning("⚠️  No pixel data in screenshot")
                return False
            
            # Check for variety in colors (not just black/white)
            unique_colors = set(pixels)
            total_pixels = len(pixels)
            
            logger.info(f"Screenshot analysis: {len(unique_colors)} unique colors out of {total_pixels} pixels")
            
            # If we have at least 3 different colors, it's probably a real screenshot
            if len(unique_colors) >= 3:
                logger.info("✅ Screen Recording permission: GRANTED")
                logger.info("   (Screenshot contains varied content)")
                return True
            elif len(unique_colors) == 1:
                # All pixels are the same color - likely a permission issue
                dominant_color = list(unique_colors)[0]
                logger.warning(f"⚠️  All pixels are the same color: {dominant_color}")
                logger.warning("   This usually indicates Screen Recording permission is denied")
                return False
            else:
                # 2 colors might be just black and white - check if it's meaningful
                colors = list(unique_colors)
                logger.info(f"Found 2 colors: {colors}")
                
                # Check if it's just black/dark colors (permission denied indicator)
                dark_colors = [c for c in colors if all(channel < 50 for channel in (c if isinstance(c, tuple) else (c, c, c)))]
                
                if len(dark_colors) == len(colors):
                    logger.warning("⚠️  Screenshot contains only dark colors - likely permission denied")
                    return False
                else:
                    logger.info("✅ Screen Recording permission: GRANTED")
                    logger.info("   (Screenshot contains some light content)")
                    return True
        else:
            logger.warning("⚠️  Screenshot failed - no image data returned")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️  Screen Recording permission test failed: {e}")
        
        # Additional specific error checks
        error_str = str(e).lower()
        if 'permission' in error_str or 'denied' in error_str or 'authorization' in error_str:
            logger.error("❌ Screen Recording permission explicitly denied")
            return False
        elif 'screen capture' in error_str:
            logger.error("❌ Screen capture not allowed") 
            return False
        else:
            logger.warning("❌ Unknown screenshot error - assuming permission denied")
            return False

def test_selenium_screenshot():
    """Test if Selenium screenshots work (these don't require Screen Recording permission)."""
    try:
        logger.info("Testing Selenium screenshot capability...")
        logger.info("NOTE: This is what the bot actually uses for main screenshots")
        
        # Try to initialize a simple webdriver for testing
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run headless for testing
        chrome_options.add_argument("--window-size=800,600")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        try:
            driver_path = None
            # 1. Check PATH for chromedriver
            found_in_path = shutil.which("chromedriver")
            if found_in_path:
                logger.info(f"🔧 Found ChromeDriver in PATH: {found_in_path}")
                driver_path = found_in_path
            else:
                # 2. Check current directory (where setup.py might place it)
                # Assuming check_macos_permissions.py is in the project root
                local_chromedriver_path = os.path.join(os.getcwd(), "chromedriver")
                if os.path.exists(local_chromedriver_path):
                    logger.info(f"🔧 Found ChromeDriver in project directory: {local_chromedriver_path}")
                    driver_path = local_chromedriver_path

            if driver_path:
                logger.info(f"🔧 Using ChromeDriver from: {driver_path}")
                service = Service(executable_path=driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # 3. Fallback to Selenium's default behavior (which worked before, despite delay)
                logger.info("🔧 ChromeDriver not found in PATH or project directory. Using Selenium's default driver management.")
                driver = webdriver.Chrome(options=chrome_options)
            
            # Navigate to a simple page
            driver.get("data:text/html,<html><body><h1>Test Page</h1></body></html>")
            time.sleep(1)
            
            # Try to take a screenshot
            driver.save_screenshot('test_selenium_screenshot.png')
            logger.info("✅ Selenium screenshot: WORKING")
            logger.info("   Saved as: test_selenium_screenshot.png")
            
            driver.quit()
            return True
            
        except Exception as driver_error:
            logger.warning(f"⚠️  Selenium screenshot test failed: {driver_error}")
            
            # Check if it's a ChromeDriver issue vs permission issue
            error_str = str(driver_error).lower()
            if 'chromedriver' in error_str or 'chrome' in error_str:
                logger.info("   This appears to be a ChromeDriver setup issue, not permissions")
                logger.info("   Run 'python setup.py' to fix ChromeDriver issues")
                return True  # Assume permissions are OK, just setup issue
            else:
                return False
                
    except ImportError:
        logger.warning("⚠️  Selenium not installed - cannot test")
        logger.info("   Run 'pip install selenium' to test Selenium screenshots")
        return True  # Can't test, assume it's OK
    except Exception as e:
        logger.warning(f"⚠️  Selenium test setup failed: {e}")
        return True  # Assume permissions are OK, just setup issue

def check_accessibility_permission():
    """Check if Accessibility permission is granted."""
    try:
        logger.info("Testing Accessibility permission...")
        
        # Test 1: Try to get current mouse position
        current_pos = pyautogui.position()
        if current_pos:
            logger.info("✅ Mouse position detection: WORKING")
        else:
            logger.warning("⚠️  Mouse position detection failed")
            return False
        
        # Test 2: Try to get screen size 
        screen_size = pyautogui.size()
        if screen_size and screen_size[0] > 0 and screen_size[1] > 0:
            logger.info("✅ Screen size detection: WORKING")
        else:
            logger.warning("⚠️  Screen size detection failed")
            return False
        
        # Test 3: Try a very small mouse movement (shouldn't affect user)
        original_pos = pyautogui.position()
        try:
            # Move mouse by 1 pixel and back
            pyautogui.move(1, 0, duration=0.1)
            pyautogui.move(-1, 0, duration=0.1)
            logger.info("✅ Mouse control: WORKING")
            logger.info("✅ Accessibility permission: GRANTED")
            return True
        except Exception as move_error:
            logger.warning(f"⚠️  Mouse movement test failed: {move_error}")
            
            # Check for specific permission-related errors
            error_str = str(move_error).lower()
            if 'permission' in error_str or 'denied' in error_str or 'accessibility' in error_str:
                logger.error("❌ Accessibility permission explicitly denied")
                return False
            else:
                logger.warning("❌ Unknown accessibility error - assuming permission denied")
                return False
                
    except Exception as e:
        logger.warning(f"⚠️  Accessibility permission test failed: {e}")
        
        # Check for specific permission-related errors
        error_str = str(e).lower()
        if 'permission' in error_str or 'denied' in error_str or 'accessibility' in error_str:
            logger.error("❌ Accessibility permission explicitly denied")
            return False
        elif 'cgevent' in error_str or 'quartz' in error_str:
            logger.error("❌ macOS accessibility framework access denied")
            return False
        else:
            logger.warning("❌ Unknown accessibility error - assuming permission denied")
            return False

def check_automation_permission():
    """Check if Automation permission is granted for controlling other apps."""
    try:
        logger.info("Testing Automation permission (AppleScript app control)...")
        
        # Test 1: Try a simple AppleScript that controls System Events
        try:
            logger.info("🔧 Testing System Events control...")
            # This AppleScript command will trigger the automation permission dialog if not granted
            applescript = '''
            tell application "System Events"
                return name of first process
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', applescript], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                logger.info("✅ AppleScript System Events control: WORKING")
                logger.info(f"   Successfully queried process: {result.stdout.strip()}")
                applescript_system_events = True
            else:
                logger.warning(f"⚠️  AppleScript System Events control failed: {result.stderr}")
                applescript_system_events = False
                
        except subprocess.TimeoutExpired:
            logger.warning("⚠️  AppleScript System Events control timed out")
            applescript_system_events = False
        except Exception as e:
            logger.warning(f"⚠️  AppleScript System Events control failed: {e}")
            applescript_system_events = False
        
        # Test 2: Try controlling a specific application (safer test)
        try:
            logger.info("🔧 Testing app control via AppleScript...")
            logger.info("   (Testing with Finder - no apps will be opened)")
            
            # Test controlling Finder (always available)
            applescript = '''
            tell application "Finder"
                return name
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', applescript], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and 'Finder' in result.stdout:
                logger.info("✅ AppleScript app control: WORKING")
                logger.info("   Successfully controlled Finder via AppleScript")
                applescript_app_control = True
            else:
                logger.warning(f"⚠️  AppleScript app control failed: {result.stderr}")
                applescript_app_control = False
                
        except Exception as e:
            logger.warning(f"⚠️  AppleScript app control test failed: {e}")
            applescript_app_control = False
        
        # Determine overall automation capability
        if applescript_system_events and applescript_app_control:
            logger.info("✅ Automation permission: GRANTED")
            logger.info("   • Can control System Events")
            logger.info("   • Can control other applications")
            return True
        elif applescript_app_control:
            logger.warning("⚠️  Automation permission: PARTIAL")
            logger.warning("   • Can control some applications")
            logger.warning("   • May need permission for System Events")
            return False
        else:
            logger.warning("❌ Automation permission: DENIED")
            logger.warning("   • Cannot control applications via AppleScript")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️  Automation permission test failed: {e}")
        return False

def check_app_launching_permission(skip_disruptive_tests=True):
    """Check if the bot can launch applications."""
    try:
        logger.info("Testing App Launching permission...")
        
        # Test 1: Try using subprocess to launch a harmless system app
        try:
            logger.info("📱 About to launch Calculator app for testing...")
            logger.info("   (Don't worry - we'll close it automatically in a moment)")
            
            # Try to open Calculator (a safe system app)
            result = subprocess.run(['open', '-a', 'Calculator'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                logger.info("✅ Calculator launched successfully")
                logger.info("✅ Subprocess app launching: WORKING")
                
                # Close Calculator quickly
                logger.info("🔄 Closing Calculator automatically...")
                time.sleep(1)
                close_result = subprocess.run(['osascript', '-e', 'tell application "Calculator" to quit'], 
                             capture_output=True, text=True, timeout=3)
                
                if close_result.returncode == 0:
                    logger.info("✅ Calculator closed successfully")
                else:
                    logger.warning("⚠️  Calculator may still be open - you can close it manually")
                
                subprocess_works = True
            else:
                logger.warning(f"⚠️  Calculator launch failed: {result.stderr}")
                logger.warning(f"⚠️  Subprocess launching failed: {result.stderr}")
                subprocess_works = False
                
        except subprocess.TimeoutExpired:
            logger.warning("⚠️  Calculator launch timed out")
            logger.warning("⚠️  App launching timed out")
            subprocess_works = False
        except Exception as e:
            logger.warning(f"⚠️  Calculator launch failed: {e}")
            logger.warning(f"⚠️  Subprocess app launching failed: {e}")
            subprocess_works = False
        
        # Test 2: Check if we can use osascript for AppleScript commands
        try:
            logger.info("Testing AppleScript execution...")
            
            # Simple AppleScript test that doesn't open anything
            result = subprocess.run(['osascript', '-e', 'return "test"'], 
                                  capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0 and 'test' in result.stdout:
                logger.info("✅ AppleScript execution: WORKING")
                applescript_works = True
            else:
                logger.warning("⚠️  AppleScript execution failed")
                applescript_works = False
                
        except Exception as e:
            logger.warning(f"⚠️  AppleScript test failed: {e}")
            applescript_works = False
        
        # Test 3: Try using subprocess to open URLs (for WhatsApp Web)
        try:
            if skip_disruptive_tests:
                logger.info("Skipping URL opening test as it may disrupt the user.")
                return True
            
            logger.info("Testing URL opening capability...")
            logger.info("📄 About to test URL opening (no actual webpage will open)...")
            
            # Test 1: Try creating a temporary HTML file and opening it
            try:
                import tempfile
                
                # Create a temporary HTML file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp_file:
                    tmp_file.write('<html><body><h1>Permission Test</h1><p>This is a test file.</p></body></html>')
                    temp_file_path = tmp_file.name
                
                logger.info(f"📄 Created temporary test file: {temp_file_path}")
                logger.info("📄 About to open temporary HTML file for testing...")
                
                # Try to open the temporary file
                result = subprocess.run(['open', temp_file_path], 
                                      capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    logger.info("✅ Temporary HTML file opened successfully")
                    logger.info("✅ URL opening: WORKING (via file opening)")
                    
                    # Give browser time to load the file before cleanup
                    logger.info("⏳ Waiting 3 seconds for browser to load file...")
                    time.sleep(3)
                    
                    # Clean up the temporary file
                    try:
                        os.unlink(temp_file_path)
                        logger.info("🧹 Temporary test file cleaned up")
                    except:
                        logger.warning(f"⚠️  Could not clean up temporary file: {temp_file_path}")
                        logger.info(f"   File location: {temp_file_path}")
                        logger.info("   You can delete it manually if needed")
                    
                    url_works = True
                else:
                    logger.warning(f"⚠️  Temporary file opening failed: {result.stderr}")
                    url_works = False
                    
                    # Clean up even if opening failed
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
                        
            except Exception as temp_error:
                logger.warning(f"⚠️  Temporary file test failed: {temp_error}")
                
                # Test 2: Fallback to testing with a simple website
                try:
                    logger.info("📄 Fallback: Testing with simple website opening...")
                    logger.info("📄 About to open example.com briefly (you can close it)...")
                    
                    result = subprocess.run(['open', 'https://example.com'], 
                                          capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0:
                        logger.info("✅ Website opened successfully")
                        logger.info("✅ URL opening: WORKING (via website opening)")
                        url_works = True
                    else:
                        logger.warning(f"⚠️  Website opening failed: {result.stderr}")
                        url_works = False
                        
                except Exception as web_error:
                    logger.warning(f"⚠️  Website opening test failed: {web_error}")
                    logger.info("ℹ️  URL opening capability could not be verified")
                    url_works = False
                
        except Exception as e:
            logger.warning(f"⚠️  URL opening test failed: {e}")
            url_works = False
        
        # Determine overall app launching capability
        if subprocess_works or applescript_works or url_works:
            logger.info("✅ App Launching permission: GRANTED")
            if subprocess_works:
                logger.info("   • Can launch desktop applications (like Calculator)")
            if applescript_works:
                logger.info("   • Can execute AppleScript commands")
            if url_works:
                logger.info("   • Can open URLs in default browser")
            return True
        else:
            logger.warning("❌ App Launching permission: LIMITED/DENIED")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️  App launching permission test failed: {e}")
        return False

def main():
    """Main permission checker function."""
    print("🔐 macOS Permission Checker for Ad Watcher Bot")
    print("=" * 50)
    
    # Check if running on macOS
    if platform.system().lower() != 'darwin':
        print("ℹ️  This utility is designed for macOS only.")
        print("   You're running on:", platform.system())
        print("   The Ad Watcher Bot should work without additional permissions.")
        return
    
    print("This utility will test permissions needed for different bot features:")
    print("• Selenium Screenshots: What the bot actually uses (no special permissions needed)")
    print("• Screen Recording: Only needed for WhatsApp detection (not main screenshots)")
    print("• Accessibility: Required for mouse clicks and keyboard input")
    print("• Automation: Required for AppleScript app control (opening WhatsApp)")
    print("• App Launching: Helpful for automatically opening WhatsApp")
    print("")
    print("⚠️  WHAT TO EXPECT DURING TESTING:")
    print("• Calculator app may briefly open and close (for app launching test)")
    print("• A small test webpage may open in your browser (closes automatically)")
    print("• You may see permission dialogs - please grant access when prompted")
    print("• Mouse may move slightly (1 pixel) to test accessibility")
    print("")
    
    # Give user time to read and position windows
    print("⏳ Starting permission checks in 5 seconds...")
    print("   (This gives you time to read the above information)")
    time.sleep(5)
    
    # Check Selenium screenshots first (what the bot actually uses)
    selenium_screenshot = test_selenium_screenshot()
    print("")
    
    # Check Screen Recording permission (only for WhatsApp detection)
    screenshot_permission = check_screenshot_permission()
    print("")
    
    # Check Accessibility permission  
    accessibility_permission = check_accessibility_permission()
    print("")
    
    # Check Automation permission (new)
    automation_permission = check_automation_permission()
    print("")
    
    # Check App Launching permission
    app_launching_permission = check_app_launching_permission(skip_disruptive_tests=False)
    print("")
    
    # Summary
    print("📋 PERMISSION CHECK SUMMARY")
    print("=" * 30)
    
    if selenium_screenshot:
        print("📊 Selenium Screenshots: ✅ WORKING")
        print("   (This is what the bot uses for main screenshots)")
    else:
        print("📊 Selenium Screenshots: ❌ FAILED")
        print("   (Check ChromeDriver setup)")
    
    if screenshot_permission:
        print("📸 Screen Recording: ✅ GRANTED")
        print("   (Only needed for WhatsApp detection)")
    else:
        print("📸 Screen Recording: ❌ DENIED")
        print("   (WhatsApp detection may not work)")
    
    if accessibility_permission:
        print("🖱️  Accessibility: ✅ GRANTED")
    else:
        print("🖱️  Accessibility: ❌ DENIED")
    
    if automation_permission:
        print("🤖 Automation: ✅ GRANTED")
        print("   (Can control other apps via AppleScript)")
    else:
        print("🤖 Automation: ❌ DENIED")
        print("   (Will see permission dialogs during WhatsApp opening)")
    
    if app_launching_permission:
        print("🚀 App Launching: ✅ GRANTED")
    else:
        print("🚀 App Launching: ❌ LIMITED/DENIED")
    
    print("")
    
    # More nuanced assessment
    critical_permissions = selenium_screenshot and accessibility_permission
    helpful_permissions = screenshot_permission and automation_permission and app_launching_permission
    
    if critical_permissions and helpful_permissions:
        print("🎉 ALL PERMISSIONS GRANTED!")
        print("   The Ad Watcher Bot should work perfectly on your system.")
        print("   You can now run: python main.py")
    elif critical_permissions:
        print("✅ CORE PERMISSIONS GRANTED!")
        print("   The Ad Watcher Bot will work with some limitations:")
        if not screenshot_permission:
            print("   • WhatsApp detection may require manual verification")
        if not automation_permission:
            print("   • You may see permission dialogs when opening WhatsApp")
        if not app_launching_permission:
            print("   • WhatsApp opening may require manual intervention")
        print("   You can run: python main.py")
    else:
        print("❌ CRITICAL PERMISSIONS MISSING!")
        print("   The Ad Watcher Bot will not work properly without these permissions.")
        print("")
        print("🔧 How to grant permissions:")
        print("1. Open System Preferences/Settings")
        print("2. Go to Security & Privacy > Privacy")
        print("3. Grant permissions to Terminal or Cursor (depending on where you ran this script)")
        print("")
        
        if not selenium_screenshot:
            print("   For Selenium Screenshots:")
            print("   - This is usually a ChromeDriver setup issue, not permissions")
            print("   - Run 'python setup.py' to fix ChromeDriver installation")
            print("")
        
        if not accessibility_permission:
            print("   For Accessibility:")
            print("   - Click 'Accessibility' in the left sidebar") 
            print("   - Check the box next to 'Terminal' or 'Cursor'")
            print("   - You may need to restart the application")
            print("   - THIS IS REQUIRED FOR THE BOT TO WORK")
            print("")
        
        if not automation_permission:
            print("   For Automation (NEW):")
            print("   - Click 'Automation' in the left sidebar")
            print("   - Find 'Terminal' or 'Cursor' in the list")
            print("   - Check the box next to 'System Events.app'")
            print("   - Also check boxes for other apps the bot needs to control")
            print("   - This prevents permission dialogs during bot execution")
            print("")
        
        if not screenshot_permission:
            print("   For Screen Recording (optional):")
            print("   - Click 'Screen Recording' in the left sidebar")
            print("   - Check the box next to 'Terminal' or 'Cursor'")
            print("   - You may need to restart the application")
            print("   - Only needed for automatic WhatsApp detection")
            print("")
        
        if not app_launching_permission:
            print("   For App Launching (optional):")
            print("   - App launching may be restricted by system security")
            print("   - The bot will fall back to manual WhatsApp opening if needed")
            print("   - No specific permission needed, but may require user interaction")
            print("")
        
        print("🔄 After granting permissions, run this script again to verify")
        print("💡 Note: You might see permission dialogs the first time you grant access")

if __name__ == "__main__":
    main() 