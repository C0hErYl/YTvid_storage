

## **YouTube Video Downloader** 🎥📥  
This is a simple **web-based YouTube video downloader** built with **Flask (Python backend)** and **HTML, JavaScript (frontend)**. It allows users to enter a YouTube link and download the video in MP4 format (up to 1080p).  

---

### **📌 Features**  
✅ User-friendly web interface  
✅ Downloads YouTube videos in MP4 format  
✅ Supports resolutions up to **1080p**  
✅ Built using **Flask** and **yt-dlp**  
    compress to zipfile, when need unzip and open / connect to a remote server to save the videos (media saver)

---

## **🛠 Installation & Setup**  

### **1️⃣ Install Dependencies**  
Make sure you have **Python 3** installed. Then, install the required packages:  
```bash
pip install flask yt-dlp
```

### **2️⃣ Run the Server**  
Start the Flask server:  
```bash
python server.py
```

### **3️⃣ Open the Web App**  
- Open **index.html** in your browser **OR**  
- Go to **http://127.0.0.1:5000/**  

---

## **📜 Usage**  
1️⃣ Enter a **YouTube video link** in the input field.  
2️⃣ Click the **"Download"** button.  
3️⃣ The video will be downloaded to your local system.  

---

## **📁 Project Structure**  
```
/youtube-downloader
│── index.html        # Frontend (HTML + JS)
│── server.py         # Backend (Flask + yt-dlp)
│── README.md         # Documentation
│── /downloads        # (Optional) Folder for storing downloaded videos
```

---

## **💡 Troubleshooting**  

### **⚠️ "yt-dlp command not found" error**  
Run:  
```bash
pip install --upgrade yt-dlp
```

### **⚠️ Video not downloading?**  
Ensure **ffmpeg** is installed (needed for merging audio & video).  

For Windows:  
1. Download `ffmpeg.exe` from [ffmpeg.org](https://ffmpeg.org/download.html).  
2. Add it to your system **PATH** environment variable.  

For macOS/Linux:  
```bash
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Ubuntu/Linux
```

---

## **📜 License**  
This project is **open-source** and free to use.  

test1: (issue: bad bot - need sign in)
use render image success deployment:
![render image success deployment](image.png)

to fix that in test 2