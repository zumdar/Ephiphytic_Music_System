#!/bin/bash
cd ~/Desktop/EMS_Plant_Music/Live_Streaming

rpicam-vid \
  --nopreview -t 0 \
  --width 1280 --height 720 \
  --framerate 30 \
  --codec yuv420 \
  -o - | \
ffmpeg \
  -f rawvideo -pixel_format yuv420p -video_size 1280x720 -framerate 30 -i - \
  -f alsa -thread_queue_size 1024 -i plughw:4,1,0 \
  -c:v libx264 -preset ultrafast -tune zerolatency -b:v 3M -g 60 \
  -c:a aac -b:a 128k -ar 44100 -ac 2 \
  -af "aresample=async=1" \
  -map 0:v:0 -map 1:a:0 \
  -f flv -flvflags no_duration_filesize "rtmp://a.rtmp.youtube.com/live2/sa5m-7jx4-vw4m-9qxz-2gmk" \
  -map 1:a:0 -c:a pcm_s16le -f alsa plughw:2,0