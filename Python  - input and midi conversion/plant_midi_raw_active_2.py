# 
# plant_midi_raw_active_ina333_ads1115.py
# 
# Plant electricity → MIDI (RAW, unquantized)
# INA333 + ADS1115 + Raspberry Pi
# 
# Adaptive noise floor (MIDIsprout-inspired)
# High sensitivity for autonomous plant music
# Drift accumulation so slow biological change produces notes
# No scale, no harmony, no sequencing (PD/Bop handles that)
# 
# MIDI notes reflect:
# Pitch - absolute electrical state
# Velocity - intensity of electrical change


import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15 import ADS1015, AnalogIn, ads1x15
import mido


# =========================
# USER-TUNABLE PARAMETERS
# =========================

SAMPLE_HZ = 40.0

ADS_GAIN = 2                 # Increase to 4 if signal is very small
SMOOTH_ALPHA = 0.18          # Voltage smoothing
DERIV_ALPHA = 0.30           # Change-rate smoothing

NOISE_ALPHA = 0.02           # Noise floor learning rate
THRESHOLD_K = 1.7            # LOWER = more notes
MIN_NOISE = 0.0005

REFRACTORY_S = 0.08          # Minimum time between notes

# Slow drift accumulation (forces notes over time)
DRIFT_ACCUM_THRESHOLD = 0.002

BASE_NOTE = 60               # Center pitch (C4-ish)
NOTE_SPAN = 36               # ± semitones (3 octaves)

NOTE_LENGTH = 0.30
MIDI_CHANNEL = 0

SEND_CC = True
CC_NUM = 74                  # Brightness / timbre
CC_RATE_HZ = 10.0


# =========================
# HELPERS
# =========================

def clamp(x, lo, hi):
    return max(lo, min(hi, x))


# =========================
# MAIN
# =========================

def main():
    # I2C + ADC
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c)
    ads.gain = ADS_GAIN
    chan = AnalogIn(ads, ads1x15.Pin.A0)

    # MIDI
    midi_out = mido.open_output()

    dt = 1.0 / SAMPLE_HZ
    last_time = time.time()

    # Signal state
    ema_v = chan.voltage
    prev_ema_v = ema_v
    ema_d = 0.0
    noise = 0.01

    drift_accum = 0.0
    last_trigger = 0.0

    last_cc = 0.0
    cc_dt = 1.0 / CC_RATE_HZ

    print("🌱 Plant MIDI ACTIVE mode running")
    print("INA333 → ADS1115 → RAW MIDI")
    print("Press Ctrl+C to stop")

    while True:
        now = time.time()
        elapsed = now - last_time
        if elapsed < dt:
            time.sleep(dt - elapsed)
            now = time.time()
        last_time = now

        # Read voltage
        v = chan.voltage

        # Smooth voltage
        ema_v = (1 - SMOOTH_ALPHA) * ema_v + SMOOTH_ALPHA * v

        # Derivative (change rate)
        raw_d = (ema_v - prev_ema_v) / dt
        prev_ema_v = ema_v
        ema_d = (1 - DERIV_ALPHA) * ema_d + DERIV_ALPHA * raw_d

        # Adaptive noise floor
        mag = abs(ema_d)
        noise = (1 - NOISE_ALPHA) * noise + NOISE_ALPHA * mag
        noise = max(noise, MIN_NOISE)
        threshold = THRESHOLD_K * noise

        # Drift accumulation (slow biology still sings)
        drift_accum += mag * dt
        force_event = False
        if drift_accum > DRIFT_ACCUM_THRESHOLD:
            drift_accum = 0.0
            force_event = True

        # Continuous CC (plant "mood")
        if SEND_CC and (now - last_cc) > cc_dt:
            last_cc = now
            cc_val = int(clamp((ema_v / 3.3) * 127, 0, 127))
            midi_out.send(
                mido.Message(
                    "control_change",
                    channel=MIDI_CHANNEL,
                    control=CC_NUM,
                    value=cc_val
                )
            )

        # Event trigger
        if (mag > threshold or force_event) and (now - last_trigger) > REFRACTORY_S:
            last_trigger = now

            # Velocity from intensity
            strength = clamp((mag - threshold) / (threshold * 2), 0.0, 1.0)
            velocity = int(25 + strength * 102)

            # Pitch from absolute plant state
            pos = clamp(ema_v / 3.3, 0.0, 1.0)
            note = int(BASE_NOTE + (pos - 0.5) * 2 * NOTE_SPAN)
            note = clamp(note, 0, 127)

            midi_out.send(
                mido.Message(
                    "note_on",
                    channel=MIDI_CHANNEL,
                    note=note,
                    velocity=velocity
                )
            )

            time.sleep(NOTE_LENGTH)

            midi_out.send(
                mido.Message(
                    "note_off",
                    channel=MIDI_CHANNEL,
                    note=note,
                    velocity=0
                )
            )

            print(
                f"event v={ema_v:.3f}V "
                f"d={ema_d:+.5f} "
                f"thr={threshold:.5f} "
                f"note={note} vel={velocity}"
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped 🌿")