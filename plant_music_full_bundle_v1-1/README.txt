Plant Music System with ADS1115 (No Amplifier)
==============================================

This system reads analog bio-signals from plants using an ADS1115,
converts them into MIDI using Python, and feeds them into Pure Data (Pd)
to generate ambient music. It also streams a video feed to YouTube.

Components:
- Raspberry Pi 5 (8GB recommended)
- ADS1115 ADC (via I2C)
- Plant clip sensors with 1M resistors in voltage divider
- Pi Camera with IR night vision
- Bluetooth or wired speaker for local output

Scripts:
--------
- plant_midi.py: Basic voltage to MIDI
- plant_midi_adv.py: Smooths signal over time
- stream.sh: Streams camera to YouTube
- plant_music.service: Enables systemd autostart

To use:
1. Place all files in `/home/pi/plant_music`
2. `sudo systemctl enable plant_music.service`
3. Reboot to launch

See PDF for full wiring diagram and setup.
