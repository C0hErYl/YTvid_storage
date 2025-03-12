from flask import Flask, request, jsonify, render_template, send_from_directory, url_for
import yt_dlp
import os
import uuid
import re
import json
import glob
from pathlib import Path
from youtube_auth import get_youtube_cookies_path

app = Flask(__name__, static_folder='static')

# Create directories if they don't exist
DOWNLOAD_DIR = os.path.join(app.static_folder, 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# File to store video metadata
VIDEOS_JSON = os.path.join(app.static_folder, 'videos.json')

# Dictionary to store video information
videos = {}

# Save videos metadata to JSON file
def save_videos_metadata():
    with open(VIDEOS_JSON, 'w') as f:
        json.dump(videos, f)
    print(f"Saved {len(videos)} videos to metadata file")

# Load videos metadata from JSON file
def load_videos_metadata():
    global videos
    if os.path.exists(VIDEOS_JSON):
        try:
            with open(VIDEOS_JSON, 'r') as f:
                videos = json.load(f)
            print(f"Loaded {len(videos)} videos from metadata file")
        except Exception as e:
            print(f"Error loading videos metadata: {e}")
            # If there's an error, we'll rescan the directory
            videos = {}
            scan_downloads_directory()

# Scan the downloads directory and update the videos dictionary
def scan_downloads_directory():
    global videos
    
    # Find all MP4 files in the downloads directory
    video_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.mp4"))
    
    print(f"Found {len(video_files)} video files in {DOWNLOAD_DIR}")
    
    # Track new videos added
    new_videos_count = 0
    
    # For files that aren't already in our videos dict, add them
    for filepath in video_files:
        filename = os.path.basename(filepath)
        video_id = os.path.splitext(filename)[0]  # Remove extension
        
        # Skip if already in our records
        if video_id in videos:
            continue
        
        # Get file size 
        file_size = os.path.getsize(filepath)
        file_size_mb = round(file_size / (1024 * 1024), 2)
        
        # Add a basic entry for this video
        videos[video_id] = {
            'id': video_id,
            'title': f"Video {video_id[:8]}",  # Use first 8 chars of ID as title
            'filename': filename,
            'duration': 0,  # We don't know the duration
            'thumbnail': '',  # No thumbnail
            'original_url': '',  # No original URL
            'file_size': file_size_mb  # File size in MB
        }
        new_videos_count += 1
    
    print(f"Added {new_videos_count} new videos from scanning directory")
    
    # Save updated metadata
    if new_videos_count > 0:
        save_videos_metadata()

def sanitize_filename(title):
    """Sanitize the filename to be safe for storage"""
    return re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')

def download_video(link):
    try:
        # Generate a unique ID for this download
        video_id = str(uuid.uuid4())
        
        # Set download options with user-agent, referer headers, and cookies to avoid bot detection
        ydl_opts = {
            "format": "best[ext=mp4]/best",  # Single file format that doesn't require merging
            "outtmpl": os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s"),  # Save with unique ID
            "noplaylist": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Referer": "https://www.youtube.com/"
            },
            "cookiesfrombrowser": ("chrome",),  # Try to use cookies from Chrome
            "verbose": True  # Add verbose output for debugging
        }
        
        # Try to get cookies file if available
        cookies_path = get_youtube_cookies_path()
        if cookies_path:
            ydl_opts["cookiefile"] = cookies_path
        
        # Get video info first
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            title = info.get('title', 'Unknown Title')
            duration = info.get('duration', 0)
            thumbnail = info.get('thumbnail', '')
            
            # Perform the download
            ydl.download([link])
        
        # Store video info
        filename = f"{video_id}.mp4"
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        
        # Get file size
        file_size = os.path.getsize(filepath)
        file_size_mb = round(file_size / (1024 * 1024), 2)
        
        videos[video_id] = {
            'id': video_id,
            'title': title,
            'filename': filename,
            'duration': duration,
            'thumbnail': thumbnail,
            'original_url': link,
            'file_size': file_size_mb  # Add file size
        }
        
        # Save updated metadata to file
        save_videos_metadata()
        
        return {
            "success": True,
            "message": "Video downloaded successfully!",
            "video_id": video_id,
            "title": title
        }
    except Exception as e:
        error_message = str(e)
        print(f"Download error: {error_message}")
        
        # If there's an ffmpeg error, provide helpful message
        if "ffmpeg is not installed" in error_message:
            return {
                "success": False,
                "message": "Download failed: FFmpeg is not installed. Please install FFmpeg or use a different format."
            }
        
        return {
            "success": False,
            "message": f"Download failed: {error_message}"
        }

@app.route("/")
def index():
    return render_template("index.html")

# Serve the static files
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    link = data.get("url", "")
    if not link:
        return jsonify({"success": False, "message": "No URL provided"}), 400

    result = download_video(link)
    return jsonify(result)

@app.route("/videos")
def list_videos():
    # Just to be safe, scan for any new videos
    scan_downloads_directory()
    return jsonify(list(videos.values()))

@app.route("/video/<video_id>")
def serve_video(video_id):
    if video_id not in videos:
        return "Video not found", 404
    
    video_info = videos[video_id]
    return render_template("video.html", video=video_info)

@app.route("/watch/<video_id>")
def watch_video(video_id):
    if video_id not in videos:
        return "Video not found", 404
    
    filename = videos[video_id]['filename']
    # Make sure to set the correct content type for video files
    return send_from_directory(DOWNLOAD_DIR, filename, mimetype='video/mp4')
    
@app.route("/debug")
def debug_info():
    """Endpoint to provide debug information"""
    # Get list of files in download directory
    files_in_download_dir = []
    try:
        files_in_download_dir = os.listdir(DOWNLOAD_DIR)
    except Exception as e:
        files_in_download_dir = [f"Error listing files: {str(e)}"]
    
    info = {
        "app_directory": os.getcwd(),
        "static_folder": app.static_folder,
        "download_directory": DOWNLOAD_DIR,
        "download_dir_exists": os.path.exists(DOWNLOAD_DIR),
        "download_dir_writable": os.access(DOWNLOAD_DIR, os.W_OK),
        "download_dir_readable": os.access(DOWNLOAD_DIR, os.R_OK),
        "files_in_download_dir": files_in_download_dir,
        "videos_count": len(videos),
        "videos_keys": list(videos.keys()),
        "routes": [str(rule) for rule in app.url_map.iter_rules()]
    }
    
    return jsonify(info)

# Create required directories
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Load existing videos metadata
load_videos_metadata()

# Scan downloads directory for video files
scan_downloads_directory()

# Changed the app.run for production use
if __name__ == "__main__":
    # Get port from environment variable or default to 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)