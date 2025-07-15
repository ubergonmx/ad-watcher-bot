#!/usr/bin/env python3
"""
Setup script for Ad Watcher Bot
This script helps you set up the project and verify dependencies.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_chrome():
    """Check if Chrome is installed."""
    chrome_paths = [
        # Windows
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        # Linux
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium-browser",
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print("✅ Chrome browser found")
            return True
    
    # Try using which/where command
    try:
        result = shutil.which("google-chrome") or shutil.which("chrome") or shutil.which("chromium-browser")
        if result:
            print("✅ Chrome browser found in PATH")
            return True
    except:
        pass
    
    print("❌ Chrome browser not found")
    print("   Please install Google Chrome from: https://www.google.com/chrome/")
    return False

def check_chromedriver():
    """Check if ChromeDriver is available."""
    try:
        result = shutil.which("chromedriver")
        if result:
            print("✅ ChromeDriver found in PATH")
            return True
    except:
        pass
    
    # Check in current directory
    if os.path.exists("chromedriver") or os.path.exists("chromedriver.exe"):
        print("✅ ChromeDriver found in project directory")
        return True
    
    # Check if webdriver-manager is available as an alternative
    try:
        import webdriver_manager
        print("✅ webdriver-manager found (will auto-download ChromeDriver)")
        return True
    except ImportError:
        pass
    
    print("❌ ChromeDriver not found")
    print("   Please download ChromeDriver from: https://chromedriver.chromium.org/")
    print("   Or install webdriver-manager: pip install webdriver-manager")
    return False

def install_dependencies():
    """Install Python dependencies from requirements.txt."""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def get_user_input(prompt, default=None, required=True, validate_func=None):
    """Get user input with validation."""
    while True:
        try:
            if default:
                user_input = input(f"{prompt} [{default}]: ").strip()
                if not user_input:
                    user_input = default
            else:
                user_input = input(f"{prompt}: ").strip()
            
            if required and not user_input:
                print("❌ This field is required. Please enter a value.")
                continue
            
            if validate_func and not validate_func(user_input):
                continue
            
            return user_input
        except KeyboardInterrupt:
            print("\n\n⚠️  Setup interrupted by user!")
            print("   Run 'python setup.py' again to continue setup")
            sys.exit(1)
        except EOFError:
            print("\n\n⚠️  Setup interrupted!")
            print("   Run 'python setup.py' again to continue setup")
            sys.exit(1)

def validate_url(url):
    """Validate URL format."""
    if not url.startswith('https://'):
        print("❌ Website URL must start with 'https://'")
        return False
    if url == 'https://':
        print("❌ Please enter a complete URL")
        return False
    return True

def validate_identity(identity):
    """Validate identity value."""
    valid_identities = ['Internship', 'VIP1', 'VIP2', 'VIP3', 'VIP4', 'VIP5', 'VIP6', 'VIP7', 'VIP8', 'VIP9']
    if identity not in valid_identities:
        print(f"❌ Invalid identity. Valid options: {', '.join(valid_identities)}")
        return False
    return True

def validate_method(method):
    """Validate method value."""
    valid_methods = ['browser', 'api']
    if method not in valid_methods:
        print(f"❌ Invalid method. Valid options: {', '.join(valid_methods)}")
        return False
    return True

def create_env_file_interactive():
    """Create .env file interactively."""
    env_path = Path(".env")
    
    if env_path.exists():
        print("✅ .env file already exists")
        overwrite = get_user_input("Do you want to reconfigure it? (y/n)", "n", required=False)
        if overwrite.lower() not in ['y', 'yes']:
            return True
    
    print("\n🔧 Let's set up your .env configuration file")
    print("   This file will store your login credentials and settings")
    print("   Press Ctrl+C at any time to exit (you can resume later)")
    print("")
    
    # Collect all required information
    config = {}
    
    print("📋 Required Settings:")
    print("=" * 30)
    
    # Website credentials
    config['WEBSITE_USERNAME'] = get_user_input("Website username (phone number)")
    config['WEBSITE_PASSWORD'] = get_user_input("Website password")
    config['FUND_PASSWORD'] = get_user_input("Fund password (for withdrawals)")
    
    # Website URL
    config['WEBSITE_URL'] = get_user_input(
        "Website URL (full URL including https://)", 
        validate_func=validate_url
    )
    
    # Working group
    config['WORKING_GROUP'] = get_user_input("WhatsApp working group name")
    
    print("\n⚙️  Optional Settings:")
    print("=" * 30)
    
    # Optional settings
    config['DEFAULT_IDENTITY'] = get_user_input(
        "Default identity (Internship, VIP1-VIP9)", 
        "Internship", 
        required=False,
        validate_func=validate_identity
    )
    
    config['DEFAULT_METHOD'] = get_user_input(
        "Default method (browser/api)", 
        "browser", 
        required=False,
        validate_func=validate_method
    )
    
    # Create .env file
    try:
        with open(env_path, 'w') as f:
            f.write("# Ad Watcher Bot Configuration\n")
            f.write("# Generated by setup.py\n")
            f.write("# MUST HAVE NO SPACES AT THE END\n\n")
            
            f.write("# Website credentials\n")
            f.write(f"WEBSITE_USERNAME={config['WEBSITE_USERNAME']}\n")
            f.write(f"WEBSITE_PASSWORD={config['WEBSITE_PASSWORD']}\n")
            f.write(f"FUND_PASSWORD={config['FUND_PASSWORD']}\n")
            f.write(f"WEBSITE_URL={config['WEBSITE_URL']}\n\n")
            
            f.write("# WhatsApp settings\n")
            f.write(f"WORKING_GROUP={config['WORKING_GROUP']}\n\n")
            
            f.write("# Optional settings\n")
            f.write(f"DEFAULT_IDENTITY={config['DEFAULT_IDENTITY']}\n")
            f.write(f"DEFAULT_METHOD={config['DEFAULT_METHOD']}\n")
        
        print("✅ .env file created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def verify_env_credentials():
    """Check if .env file has been configured with real credentials."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found")
        return False
    
    try:
        with open(env_path, 'r') as f:
            content = f.read()
            
        # Check if file contains default placeholder values
        default_placeholders = [
            "your_username_here",
            "your_password_here", 
            "your_fund_password_here",
            "AKQA Working Group #",
            "website_url"
        ]
        
        has_placeholders = any(placeholder in content for placeholder in default_placeholders)
        if has_placeholders:
            print("⚠️  .env file contains default placeholder values")
            print("   Please update .env with your actual credentials")
            return False
        
        # Parse environment variables
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        variables = {}
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                variables[key.strip()] = value.strip().strip('"').strip("'")
        
        # Check required variables
        required_vars = [
            'WEBSITE_USERNAME',
            'WEBSITE_PASSWORD', 
            'FUND_PASSWORD',
            'WORKING_GROUP',
            'WEBSITE_URL'
        ]
        
        missing_vars = []
        empty_vars = []
        
        for var in required_vars:
            if var not in variables:
                missing_vars.append(var)
            elif not variables[var]:
                empty_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing required variables in .env: {', '.join(missing_vars)}")
            return False
        
        if empty_vars:
            print(f"⚠️  Empty values for required variables: {', '.join(empty_vars)}")
            return False
        
        # Validate specific variables
        if not variables['WEBSITE_URL'].startswith('https://'):
            print("⚠️  WEBSITE_URL should start with 'https://'")
            return False
        
        if variables['WORKING_GROUP'] and not variables['WORKING_GROUP'].replace("'", "").replace('"', '').strip():
            print("⚠️  WORKING_GROUP appears to be empty")
            return False
        
        # Check optional variables
        optional_vars = ['DEFAULT_IDENTITY', 'DEFAULT_METHOD']
        for var in optional_vars:
            if var in variables and variables[var]:
                print(f"✅ {var} = {variables[var]}")
        
        # Validate DEFAULT_IDENTITY if present
        if 'DEFAULT_IDENTITY' in variables and variables['DEFAULT_IDENTITY']:
            valid_identities = ['Internship', 'VIP1', 'VIP2', 'VIP3', 'VIP4', 'VIP5', 'VIP6', 'VIP7', 'VIP8', 'VIP9']
            if variables['DEFAULT_IDENTITY'] not in valid_identities:
                print(f"⚠️  DEFAULT_IDENTITY '{variables['DEFAULT_IDENTITY']}' is not in valid list: {valid_identities}")
        
        # Validate DEFAULT_METHOD if present
        if 'DEFAULT_METHOD' in variables and variables['DEFAULT_METHOD']:
            valid_methods = ['browser', 'api']
            if variables['DEFAULT_METHOD'] not in valid_methods:
                print(f"⚠️  DEFAULT_METHOD '{variables['DEFAULT_METHOD']}' is not in valid list: {valid_methods}")
        
        print("✅ .env file configured with credentials")
        print(f"   Username: {variables['WEBSITE_USERNAME'][:3]}...")
        print(f"   Working Group: {variables['WORKING_GROUP']}")
        print(f"   Website URL: {variables['WEBSITE_URL']}")
        return True
        
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def check_whatsapp():
    """Check if WhatsApp Desktop is installed."""
    whatsapp_paths = [
        # Windows
        os.path.expanduser("~/AppData/Local/WhatsApp/WhatsApp.exe"),
        r"C:\Users\%USERNAME%\AppData\Local\WhatsApp\WhatsApp.exe",
        # macOS
        "/Applications/WhatsApp.app",
        # Linux (WhatsApp Web will be used as fallback)
    ]
    
    for path in whatsapp_paths:
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            print("✅ WhatsApp Desktop found")
            return True
    
    print("⚠️  WhatsApp Desktop not found")
    print("   The bot will try to use WhatsApp Web as fallback")
    print("   For better reliability, install WhatsApp Desktop: https://www.whatsapp.com/download/")
    return True  # Not critical

def check_tesseract():
    """Check if Tesseract OCR engine is installed (required by pytesseract)."""
    try:
        # Try to find tesseract executable
        tesseract_cmd = shutil.which("tesseract")
        if tesseract_cmd:
            print("✅ Tesseract OCR engine found")
            
            # Try to get version to verify it works
            try:
                result = subprocess.run([tesseract_cmd, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    print(f"   Version: {version_line}")
                    return True
            except Exception as e:
                print(f"⚠️  Tesseract found but version check failed: {e}")
        
        print("⚠️  Tesseract OCR engine not found")
        print("   This is optional - used for enhanced WhatsApp detection")
        print("   The bot will work without it, but may require manual verification")
        print("")
        print("   To install Tesseract:")
        
        # Platform-specific installation instructions
        if sys.platform.startswith('darwin'):  # macOS
            print("   macOS: brew install tesseract")
        elif sys.platform.startswith('win'):  # Windows
            print("   Windows: Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        elif sys.platform.startswith('linux'):  # Linux
            print("   Ubuntu/Debian: sudo apt-get install tesseract-ocr")
            print("   CentOS/RHEL: sudo yum install tesseract")
        
        return False  # Optional, so don't fail setup
        
    except Exception as e:
        print(f"⚠️  Error checking Tesseract: {e}")
        return False

def check_macos_permissions():
    """Check if macOS permissions utility is available."""
    if not sys.platform.startswith('darwin'):
        return True
    
    if os.path.exists('check_macos_permissions.py'):
        print("✅ macOS permissions utility found")
        print("   Run 'python check_macos_permissions.py' to verify system permissions")
        return True
    else:
        print("⚠️  macOS permissions utility not found")
        print("   This is optional but recommended for macOS users")
        return True

def create_setup_progress_file():
    """Create a progress file to track setup completion."""
    try:
        with open('.setup_progress', 'w') as f:
            f.write("setup_incomplete\n")
    except Exception:
        pass

def remove_setup_progress_file():
    """Remove the progress file when setup is complete."""
    try:
        if os.path.exists('.setup_progress'):
            os.remove('.setup_progress')
    except Exception:
        pass

def check_incomplete_setup():
    """Check if there's an incomplete setup."""
    if os.path.exists('.setup_progress'):
        print("⚠️  Previous setup was incomplete!")
        print("   Continuing with setup process...")
        return True
    return False

def main():
    """Main setup function."""
    print("🤖 Ad Watcher Bot Setup")
    print("=" * 50)
    
    # Check for incomplete setup
    check_incomplete_setup()
    
    # Create progress file
    create_setup_progress_file()
    
    all_checks_passed = True
    
    try:
        # Check Python version
        if not check_python_version():
            all_checks_passed = False
        
        # Check Chrome browser
        if not check_chrome():
            all_checks_passed = False
        
        # Check ChromeDriver
        if not check_chromedriver():
            all_checks_passed = False
        
        # Install dependencies
        if not install_dependencies():
            all_checks_passed = False
        
        # Create .env file interactively
        if not create_env_file_interactive():
            all_checks_passed = False
        
        # Check WhatsApp
        check_whatsapp()
        
        # Check Tesseract OCR (optional)
        check_tesseract()
        
        # Check macOS permissions utility (optional)
        check_macos_permissions()
        
        print("\n" + "=" * 50)
        
        if all_checks_passed:
            print("🎉 Setup completed successfully!")
            print("\n📝 Next steps:")
            print("1. Your .env file has been configured with your credentials")
            print("2. Run the bot: python main.py")
            print("3. Monitor the console output for any issues")
            print("")
            print("💡 Optional enhancements:")
            print("• Install Tesseract OCR for better WhatsApp detection")
            if sys.platform.startswith('darwin'):
                print("• Run 'python check_macos_permissions.py' on macOS to verify permissions")
            print("")
            print("🔧 Bot usage options:")
            print("• Basic run: python main.py")
            print("• API mode: python main.py --api")
            print("• Complete all steps: python main.py -c")
            print("• API + complete: python main.py --api -c")
            
            # Final credential check
            if verify_env_credentials():
                print("\n🚀 You're ready to run the bot!")
                # Remove progress file on successful completion
                remove_setup_progress_file()
            else:
                print("\n⚠️  Please fix the .env configuration issues above")
                print("   Run 'python setup.py' again to reconfigure")
        else:
            print("❌ Setup incomplete. Please fix the issues above and run setup again.")
            print("   Your progress has been saved - just run 'python setup.py' again")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user!")
        print("   Your progress has been saved.")
        print("   Run 'python setup.py' again to continue from where you left off")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        print("   Run 'python setup.py' again to retry")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())