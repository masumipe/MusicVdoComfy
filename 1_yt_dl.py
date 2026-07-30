import yt_dlp

# Specify the URL of the YouTube video you want to download
url = 'https://www.youtube.com/watch?v=sqJ2QhjBQaw'
output_directory = './outputs'  # Change this to your desired download directory
# Set up the ytdlp options
options = {
    'format': 'mp4',  # Download the best available format
    'outtmpl': f'{output_directory}/yt_vdo.mp4',  # Save the file with the video title in the specified directory
}

# Use ytdlp to download the video
with yt_dlp.YoutubeDL(options) as ydl:
    ydl.download([url])
