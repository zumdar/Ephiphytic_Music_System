# diagnostic_plant_midi.py - Plot + MIDI preview from plant biosignals
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15 import ADS1015, AnalogIn, ads1x15
import mido
import matplotlib.pyplot as plt
from collections import deque

# MIDI channel and CC config
MIDI_CHANNEL = 0  # 0–15
CC_NUM = 1        # MIDI CC number

# Init I2C ADC
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
chan = AnalogIn(ads, ads1x15.Pin.A0)

# Init MIDI
outport = mido.open_output()

# Setup plot
plt.ion()
fig, ax = plt.subplots()
data = deque([0]*100, maxlen=100)
line, = ax.plot(data)
ax.set_ylim(0, 3.3)
ax.set_ylabel('Voltage (V)')
ax.set_title('Live Plant Signal')

# Loop
while True:
    voltage = chan.voltage
    data.append(voltage)
    line.set_ydata(data)
    line.set_xdata(range(len(data)))
    ax.set_ylim(0, 3.3)
    fig.canvas.draw()
    fig.canvas.flush_events()

    # Send MIDI
    midi_value = int((voltage / 3.3) * 127)
    msg = mido.Message('control_change', channel=MIDI_CHANNEL, control=CC_NUM, value=midi_value)
    outport.send(msg)
    print(f"Voltage: {voltage:.2f}V -> MIDI: {midi_value}")

    time.sleep(0.25)


