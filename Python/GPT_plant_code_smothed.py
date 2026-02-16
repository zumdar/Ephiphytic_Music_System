# GPT plant code smoothed 

# plant_midi_adv.py - Advanced signal processing for plant-to-MIDI using ADS1115
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15 import ADS1015, AnalogIn, ads1x15
import mido
import numpy as np

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
chan = AnalogIn(ads, ads1x15.Pin.A0)

outport = mido.open_output()
history = []

def smooth(data, window_size=5):
    if len(data) < window_size:
        return data[-1]
    return np.mean(data[-window_size:])

while True:
    voltage = chan.voltage
    history.append(voltage)
    smoothed = smooth(history)
    midi_value = int((smoothed / 3.3) * 127)
    midi_value = max(0, min(127, midi_value))
    msg = mido.Message('note_on', note=midi_value, velocity=100)
    outport.send(msg)
    print(f"Smoothed Voltage: {smoothed:.2f}V -> MIDI: {midi_value}")
    time.sleep(0.1)



