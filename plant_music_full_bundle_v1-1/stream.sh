#!/bin/bash
# stream.sh - Start FFmpeg stream from Pi camera to YouTube

ffmpeg -f v4l2 -i /dev/video0 -f lavfi -i anullsrc -c:v libx264 -preset veryfast -maxrate 2000k -bufsize 4000k -pix_fmt yuv420p -g 50 -c:a aac -b:a 128k -ar 44100 -f flv "rtmp://a.rtmp.youtube.com/live2/YOUR_STREAM_KEY"
