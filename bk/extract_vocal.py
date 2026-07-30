import subprocess

# Specify the input file and output file names
input_file = 'outputs/yt_vdo.mp4'
output_file = 'outputs/vocal.mp3'

# Set up the ffmpeg command
command = ['ffmpeg', '-i', input_file, '-q:a', '0', '-map', 'a', output_file]

# Run the ffmpeg command
subprocess.run(command)
