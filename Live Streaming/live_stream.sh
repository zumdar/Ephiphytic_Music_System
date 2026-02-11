libcamera-vid -t 0 --inline --width 1920 --height 1080 --framerate 30 -o - | \
ffmpeg -f h264 -i - \
-f pulse -i default \
-c:v copy \
-c:a aac -b:a 256k -ar 44100 -ac 2 \
-af "pan=stereo|c0=c0|c1=c1" \
-f flv rtmp://a.rtmp.youtube.com/live2/sa5m-7jx4-vw4m-9qxz-2gmk
