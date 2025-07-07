import subprocess

applescript1 = '''
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
    # subprocess.run(logger.info("Trying to open WhatsApp Desktop app...")
    result = subprocess.run(['open', '-a', 'WhatsApp'], 
                            capture_output=True, text=True, timeout=10)
    
    if result.returncode == 0:
        print("✅ WhatsApp Desktop opened via subprocess")
        subprocess.run(
            ['osascript', '-e', applescript1],
            capture_output=True, text=True, timeout=10, check=True
        )
        print("AppleScript executed successfully.")
    else:
        print(f"WhatsApp Desktop not found: {result.stderr}")
except subprocess.CalledProcessError as e:
    print(f"An error occurred during AppleScript execution: {e.stderr}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

