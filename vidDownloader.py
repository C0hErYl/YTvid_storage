# import yt_dlp

# link = "https://youtu.be/iwhTPrtNdsI"
# def download_video(link):
#     try:
#         ydl_opts = {
#             "format": "mp4[height<=1080]",  # Ensures a single MP4 file with both audio and video
#         }
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             ydl.download([link])
#         print("Video downloaded successfully!")

#     except Exception as e:
#         print(f"Download failed: {e}")

# download_video(link)
