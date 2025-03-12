from flask import Flask, request, jsonify, render_template, send_from_directory
import yt_dlp
import os
import uuid
import re
import json
import glob
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('youtube-downloader')

app = Flask(__name__, static_folder='static')

# Create directories if they don't exist
DOWNLOAD_DIR = os.path.join(app.static_folder, 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# File to store video metadata
VIDEOS_JSON = os.path.join(app.static_folder, 'videos.json')

# Dictionary to store video information
videos = {}

def save_videos_metadata():
    """Save videos metadata to JSON file"""
    try:
        with open(VIDEOS_JSON, 'w') as f:
            json.dump(videos, f)
        logger.info(f"Saved {len(videos)} videos to metadata file")
    except Exception as e:
        logger.error(f"Error saving videos metadata: {e}")

def load_videos_metadata():
    """Load videos metadata from JSON file"""
    global videos
    if os.path.exists(VIDEOS_JSON):
        try:
            with open(VIDEOS_JSON, 'r') as f:
                videos = json.load(f)
            logger.info(f"Loaded {len(videos)} videos from metadata file")
        except Exception as e:
            logger.error(f"Error loading videos metadata: {e}")
            videos = {}
            scan_downloads_directory()

def scan_downloads_directory():
    """Scan the downloads directory and update the videos dictionary"""
    global videos
    
    # Find all video files in the downloads directory
    video_extensions = ['mp4', 'webm', 'mkv']
    video_files = []
    for ext in video_extensions:
        video_files.extend(glob.glob(os.path.join(DOWNLOAD_DIR, f"*.{ext}")))
    
    logger.info(f"Found {len(video_files)} video files in {DOWNLOAD_DIR}")
    
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
    
    logger.info(f"Added {new_videos_count} new videos from scanning directory")
    
    # Save updated metadata
    if new_videos_count > 0:
        save_videos_metadata()

def sanitize_filename(title):
    """Sanitize the filename to be safe for storage"""
    return re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')

def get_cookie_file():
    """Get path to YouTube cookies file"""
    cookie_files = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'youtube_cookies.txt'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.txt')
    ]
    
    for cookie_file in cookie_files:
        if os.path.exists(cookie_file):
            logger.info(f"Using cookie file: {cookie_file}")
            return cookie_file
    
    logger.warning("No cookie file found. This may cause authentication issues.")
    return None

def list_available_formats(url):
    """List available formats for a given URL"""
    logger.info(f"Checking available formats for: {url}")
    
    format_opts = {
        "skip_download": True,
        "listformats": True,
        "quiet": True,
        "no_warnings": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Referer": "https://www.youtube.com/"
        }
    }
    
    cookie_file = get_cookie_file()
    if cookie_file:
        format_opts["cookiefile"] = cookie_file
    
    formats = []
    try:
        with yt_dlp.YoutubeDL(format_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info and 'formats' in info:
                return info['formats']
    except Exception as e:
        logger.error(f"Error listing formats: {e}")
    
    return formats

def download_video(link):
    """Download a video from the given link"""
    try:
        # Generate a unique ID for this download
        video_id = str(uuid.uuid4())
        
        # First, check available formats
        formats = list_available_formats(link)
        logger.info(f"Found {len(formats)} formats for {link}")
        
        # Set up download options
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",  # More flexible format selection
            "outtmpl": os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s"),
            "noplaylist": True,
            "merge_output_format": "mp4",
            "ignoreerrors": True,
            "no_warnings": False,
            "verbose": True,
            "geo_bypass": True,
            "postprocessor_args": {
                'ffmpeg': ['-c:v', 'libx264', '-c:a', 'aac']
            },
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],
                }
            },
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.youtube.com/"
            }
        }
        
        # Add cookies if available
        cookie_file = get_cookie_file()
        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file
        
        # Download the video
        logger.info(f"Starting download for {link}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            
            if not info:
                raise Exception("Failed to extract video information")
                
            title = info.get('title', 'Unknown Title')
            duration = info.get('duration', 0)
            thumbnail = info.get('thumbnail', '')
            
            logger.info(f"Download completed for '{title}'")
        
        # Find the downloaded file
        downloaded_files = glob.glob(os.path.join(DOWNLOAD_DIR, f"{video_id}.*"))
        if not downloaded_files:
            raise Exception("File was not downloaded correctly")
        
        filepath = downloaded_files[0]
        filename = os.path.basename(filepath)
        
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
            'file_size': file_size_mb
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
        logger.error(f"Download error: {error_message}")
        
        # Provide specific error messages based on the error
        if "ffmpeg is not installed" in error_message:
            return {
                "success": False,
                "message": "Download failed: FFmpeg is not installed. Please install FFmpeg or use a different format."
            }
        
        if "Requested format is not available" in error_message:
            return {
                "success": False,
                "message": "Could not find the requested video format. The video might be restricted or unavailable."
            }
        
        if "Sign in to confirm you're not a bot" in error_message:
            return {
                "success": False, 
                "message": "YouTube requires authentication. Your cookies may be invalid or expired. Please update your youtube_cookies.txt file."
            }
        
        if "This video is available for Premium users only" in error_message or "This video is only available for Premium users" in error_message:
            return {
                "success": False,
                "message": "This video requires a YouTube Premium subscription."
            }
        
        if "Private video" in error_message:
            return {
                "success": False,
                "message": "This video is private and cannot be accessed."
            }
        
        if "Video unavailable" in error_message:
            return {
                "success": False,
                "message": "This video is unavailable. It may have been removed or set to private."
            }
        
        return {
            "success": False,
            "message": f"Download failed: {error_message}"
        }

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route("/download", methods=["POST"])
def download():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Invalid request data"}), 400
            
        link = data.get("url", "")
        if not link:
            return jsonify({"success": False, "message": "No URL provided"}), 400

        result = download_video(link)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in download route: {str(e)}")
        return jsonify({
            "success": False, 
            "message": f"Server error: {str(e)}"
        }), 500

# Add this route to your server.py file
@app.route("/delete/<video_id>", methods=["POST"])
def delete_video(video_id):
    """Delete a video from the library"""
    try:
        if video_id not in videos:
            return jsonify({"success": False, "message": "Video not found"}), 404
        
        # Get the filename before removing from dictionary
        filename = videos[video_id]['filename']
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        
        # Try to delete the file
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted file: {filepath}")
            else:
                logger.warning(f"File not found for deletion: {filepath}")
        except Exception as e:
            logger.error(f"Error deleting file {filepath}: {e}")
            # We'll still remove it from the dictionary even if file deletion fails
        
        # Remove from our videos dictionary
        del videos[video_id]
        
        # Save updated metadata
        save_videos_metadata()
        
        return jsonify({
            "success": True,
            "message": "Video deleted successfully"
        })
    except Exception as e:
        logger.error(f"Error in delete_video route: {str(e)}")
        return jsonify({
            "success": False, 
            "message": f"Error deleting video: {str(e)}"
        }), 500
    
@app.route("/videos")
def list_videos():
    try:
        # Scan for any new videos
        scan_downloads_directory()
        return jsonify(list(videos.values()))
    except Exception as e:
        logger.error(f"Error listing videos: {str(e)}")
        return jsonify([]), 500

@app.route("/video/<video_id>")
def serve_video(video_id):
    if video_id not in videos:
        return "Video not found", 404
    
    video_info = videos[video_id]
    return render_template("video.html", video=video_info)

@app.route("/watch/<video_id>")
def watch_video(video_id):
    if video_id not in videos:
        logger.error(f"Video ID {video_id} not found in videos dictionary")
        return "Video not found", 404
    
    filename = videos[video_id]['filename']
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    # Check if file exists and logs
    file_exists = os.path.exists(filepath)
    logger.info(f"File {filepath} exists: {file_exists}")
    
    if not file_exists:
        logger.error(f"File {filepath} does not exist")
        return "Video file not found", 404
    
    # Determine content type based on file extension
    content_type = "video/mp4"
    if filename.endswith(".webm"):
        content_type = "video/webm"
    elif filename.endswith(".mkv"):
        content_type = "video/x-matroska"
    
    logger.info(f"Serving video {video_id} with content type {content_type}")
    return send_from_directory(DOWNLOAD_DIR, filename, mimetype=content_type)
    

@app.route("/debug")
def debug_info():
    """Endpoint to provide debug information"""
    try:
        # Get list of files in download directory
        files_in_download_dir = []
        try:
            files_in_download_dir = os.listdir(DOWNLOAD_DIR)
        except Exception as e:
            files_in_download_dir = [f"Error listing files: {str(e)}"]
        
        # Check for missing files
        missing_files = []
        for video_id, video_info in videos.items():
            filepath = os.path.join(DOWNLOAD_DIR, video_info['filename'])
            if not os.path.exists(filepath):
                missing_files.append(video_info['filename'])
        
        # Check cookie files
        cookie_files = [
            "youtube_cookies.txt",
            "cookies.txt"
        ]
        cookie_status = {}
        for cf in cookie_files:
            cookie_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cf)
            exists = os.path.exists(cookie_path)
            size = 0
            if exists:
                size = os.path.getsize(cookie_path)
            cookie_status[cf] = {
                "exists": exists,
                "size_bytes": size,
                "readable": os.access(cookie_path, os.R_OK) if exists else False
            }
        
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
            "missing_files": missing_files,
            "cookie_files": cookie_status,
            "routes": [str(rule) for rule in app.url_map.iter_rules()],
            "yt_dlp_version": yt_dlp.version.__version__
        }
        
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error in debug route: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/embed/<video_id>")
def embed_video(video_id):
    """Embed a YouTube video directly"""
    if video_id not in videos:
        return "Video not found", 404
    
    video_info = videos[video_id]
    youtube_id = None
    
    # Try to extract YouTube ID from the original URL
    if video_info['original_url']:
        try:
            youtube_regex = r'(?:youtu\.be/|youtube\.com/(?:embed/|v/|watch\?v=|watch\?.+&v=))([^&?/]+)'
            match = re.search(youtube_regex, video_info['original_url'])
            if match:
                youtube_id = match.group(1)
        except Exception as e:
            logger.error(f"Error extracting YouTube ID: {e}")
    
    return render_template("embed.html", video=video_info, youtube_id=youtube_id)



# Create required directories
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Load existing videos metadata
load_videos_metadata()

# Scan downloads directory for video files
scan_downloads_directory()

if __name__ == "__main__":
    # Get port from environment variable or default to 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)