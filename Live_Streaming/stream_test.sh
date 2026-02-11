# 10-second test with audio + video
rpicam-vid -t 10000 --nopreview --inline --width 1920 --height 1080 -o - | \
ffmpeg -f h264 -i - \
-f pulse -i default \
-c:v copy -c:a aac -b:a 128k \
test_stream.mp4

# Check the file
ls -lh test_stream.mp4
ffplay test_stream.mp4