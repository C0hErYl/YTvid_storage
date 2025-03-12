import os
import subprocess
import json
from pathlib import Path

COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'youtube_cookies.txt')

def extract_cookies_from_chrome():
    """Extract YouTube cookies from Chrome browser via yt-dlp's browser cookie feature."""
    try:
        # This will attempt to extract cookies from the Chrome browser
        subprocess.run(
            ["yt-dlp", "--cookies-from-browser", "chrome", "-o", "temp", "--skip-download", "https://www.youtube.com"],
            check=True,
            capture_output=True
        )
        print("Browser cookies extracted successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error extracting browser cookies: {e}")
        print(f"stdout: {e.stdout.decode()}")
        print(f"stderr: {e.stderr.decode()}")
        return False

def get_youtube_cookies_path():
    """Get path to YouTube cookies file or attempt to create one."""
    
    # If cookie file already exists, return it
    if os.path.exists(COOKIE_FILE):
        return COOKIE_FILE
    
    # Try to extract cookies from browser
    if extract_cookies_from_chrome():
        # Find cookies file that was created
        cookie_files = list(Path(".").glob("*.txt"))
        if cookie_files:
            # Move first found cookie file to our standard location
            os.rename(str(cookie_files[0]), COOKIE_FILE)
            print(f"Cookie file saved to {COOKIE_FILE}")
            return COOKIE_FILE
    
    print("Warning: Could not create cookie file. Some videos may be inaccessible.")
    return None