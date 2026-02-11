#!/bin/bash
cd ~/Desktop/EMS_Plant_Music/Live_Streaming

rpicam-vid \
  --nopreview -t 0 \
  --width 1920 --height 1080 \
  --framerate 30 \
  --codec h264 \
  --bitrate 6000000 \
  --inline \
  --libav-format mpegts \
  -o - | \
ffmpeg \
  -thread_queue_size 512 \
  -i - \
  -thread_queue_size 512 \
  -f pulse -ar 48000 -i default \
  -c:v copy \
  -c:a aac -b:a 160k -ar 44100 \
  -f flv "rtmp://a.rtmp.youtube.com/live2/sa5m-7jx4-vw4m-9qxz-2gmk"
