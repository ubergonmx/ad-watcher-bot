#!/usr/bin/env python3
"""
Coordinate Finder Utility
This script helps you find the correct coordinates for WhatsApp interface elements.
Move your mouse to different parts of WhatsApp and note the coordinates displayed.
"""

import pyautogui
import time
import sys

def main():
    """Main coordinate finder function."""
    print("🎯 Coordinate Finder for Ad Watcher Bot")
    print("=" * 50)
    print("Instructions:")
    print("1. Open WhatsApp Desktop or WhatsApp Web")
    print("2. Maximize the WhatsApp window")
    print("3. Move your mouse to different elements:")
    print("   - Search bar (for contact searching)")
    print("   - Contact list area")  
    print("   - Message input area")
    print("4. Note down the coordinates displayed below")
    print("5. Press Ctrl+C to exit")
    print("\n" + "=" * 50)
    print("Move your mouse around WhatsApp interface:")
    print()
    
    try:
        while True:
            # Get current mouse position
            x, y = pyautogui.position()
            
            # Create a position string
            position_str = f"X: {str(x).rjust(4)} Y: {str(y).rjust(4)}"
            
            # Print position with carriage return to update same line
            print(f"\r{position_str}", end='', flush=True)
            
            # Small delay to avoid overwhelming the output
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n📝 How to use these coordinates:")
        print("1. Open main.py in your text editor")
        print("2. Find the navigate_and_send_message() method")
        print("3. Update these lines with your coordinates:")
        print("   - pyautogui.click(105, 105)  # Search area")
        print("   - pyautogui.click(205, 205)  # Contact selection")
        print("   - pyautogui.click(930, 930)  # Message input")
        print("\n💡 Tips:")
        print("- Search area: Usually top-left of WhatsApp")
        print("- Contact area: Where contacts appear in search results")
        print("- Message input: Bottom area where you type messages")
        print("\nCoordinate finder stopped. Good luck with your bot! 🤖")

if __name__ == "__main__":
    main() 