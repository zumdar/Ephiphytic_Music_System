#!/bin/bash
cd ~/Desktop/EMS_Plant_Music/Live_Streaming

#working ok. 2/14/2026

# Make sure Pure Data is set to output to hw:Loopback,0 or plughw:3,0

killall alsaloop 2>/dev/null
killall arecord 2>/dev/null
killall aplay 2>/dev/null

rm -f /tmp/audio_pipe
mkfifo /tmp/audio_pipe

arecord -D hw:2,1,0 -f S32_LE -r 48000 -c 4 --buffer-size=65536 --period-size=8192 2>/dev/null | \
tee /tmp/audio_pipe | \
aplay -D plughw:4,0 -f S32_LE -r 48000 -c 2 --buffer-size=65536 --period-size=8192 2>/dev/null &
AUDIO_PID=$!

sleep 3

trap "kill $AUDIO_PID 2>/dev/null; rm -f /tmp/audio_pipe" EXIT

rpicam-vid \
  --nopreview -t 0 \
  --width 1280 --height 720 \
  --framerate 30 \
  --codec yuv420 \
  -o - | \
ffmpeg \
  -f rawvideo -pixel_format yuv420p -video_size 1280x720 -framerate 30 -i - \
  -f s32le -ac 4 -ar 48000 -thread_queue_size 8192 -i /tmp/audio_pipe \
  -c:v libx264 -preset ultrafast -tune zerolatency -b:v 3M -g 60 \
  -c:a aac -b:a 128k -ar 44100 -ac 2 \
  -af "aresample=async=1:min_hard_comp=0.100000" \
  -map 0:v:0 -map 1:a:0 \
  -f flv -flvflags no_duration_filesize "rtmp://a.rtmp.youtube.com/live2/qum1-8wqm-qj6m-15wx-0zyj"