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

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_path = Path(".env")
    example_path = Path("env.example")
    
    if env_path.exists():
        print("✅ .env file already exists")
        return True
    
    if not example_path.exists():
        print("❌ env.example file not found")
        return False
    
    try:
        shutil.copy("env.example", ".env")
        print("✅ Created .env file from template")
        print("   ⚠️  Please edit .env file and add your credentials!")
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
            
        if "your_username_here" in content or "your_password_here" in content:
            print("⚠️  .env file contains default values")
            print("   Please update .env with your actual credentials")
            return False
        
        # Check if variables are defined
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        variables = {}
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                variables[key.strip()] = value.strip()
        
        if 'WEBSITE_USERNAME' not in variables or 'WEBSITE_PASSWORD' not in variables:
            print("❌ Required variables not found in .env file")
            return False
        
        if not variables['WEBSITE_USERNAME'] or not variables['WEBSITE_PASSWORD']:
            print("⚠️  Credentials appear to be empty in .env file")
            return False
        
        print("✅ .env file configured with credentials")
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

def main():
    """Main setup function."""
    print("🤖 Ad Watcher Bot Setup")
    print("=" * 50)
    
    all_checks_passed = True
    
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
    
    # Create .env file
    if not create_env_file():
        all_checks_passed = False
    
    # Check WhatsApp
    check_whatsapp()
    
    # Check Tesseract OCR (optional)
    check_tesseract()
    
    print("\n" + "=" * 50)
    
    if all_checks_passed:
        print("🎉 Setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Edit .env file with your login credentials")
        print("2. Run the bot: python main.py")
        print("3. Monitor the console output for any issues")
        print("")
        print("💡 Optional enhancements:")
        print("• Install Tesseract OCR for better WhatsApp detection")
        print("• Run 'python check_macos_permissions.py' on macOS to verify permissions")
        
        # Final credential check
        if verify_env_credentials():
            print("\n🚀 You're ready to run the bot!")
        else:
            print("\n⚠️  Please configure your credentials in .env before running")
    else:
        print("❌ Setup incomplete. Please fix the issues above and run setup again.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 