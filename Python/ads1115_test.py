import time

import board

from adafruit_ads1x15 import ADS1015, AnalogIn, ads1x15

# Create the I2C bus
i2c = board.I2C()

# Create the ADC object using the I2C bus
ads = ADS1015(i2c)

# Create single-ended input on channel 0
chan = AnalogIn(ads, ads1x15.Pin.A0)

# Create differential input between channel 0 and 1
# chan = AnalogIn(ads, ads1x15.Pin.A0, ads1x15.Pin.A1)

print("{:>5}\t{:>5}".format("raw", "v"))

while True:
    print("{:>5}\t{:>5.3f}".format(chan.value, chan.voltage))
    time.sleep(0.5)