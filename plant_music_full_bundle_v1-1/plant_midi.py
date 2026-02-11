# plant_midi.py - Basic plant signal to MIDI converter using ADS1115
# Requirements: adafruit-circuitpython-ads1x15, mido, python-rtmidi

import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import mido

# Initialize I2C and ADC
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
chan = AnalogIn(ads, ADS.P0)

# Setup MIDI output
outport = mido.open_output()  # Or use mido.open_output('IAC Driver Bus 1') if named

while True:
    voltage = chan.voltage
    midi_value = int((voltage / 3.3) * 127)
    midi_value = max(0, min(127, midi_value))
    msg = mido.Message('control_change', control=1, value=midi_value)
    outport.send(msg)
    print(f"Voltage: {voltage:.2f}V -> MIDI: {midi_value}")
    time.sleep(0.5)
