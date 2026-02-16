# Test the arecord/aplay pipe separately while Pure Data is playing
arecord -D hw:3,1,0 -f S32_LE -r 48000 -c 4 --buffer-size=65536 --period-size=8192 | \
aplay -D plughw:2,0 -f S32_LE -r 48000 -c 2 --buffer-size=65536 --period-size=8192