# More "on-the-grid" midi note output
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
from adafruit_ads1x15 import AnalogIn, ads1x15
import mido
import subprocess
import re


# =========================
# USER-TUNABLE PARAMETERS (Simpler, pre-random/threading version)
# =========================

SAMPLE_HZ = 40.0

ADS_GAIN = 2
SMOOTH_ALPHA = 0.18
DERIV_ALPHA = 0.30

NOISE_ALPHA = 0.02
THRESHOLD_K = 0.5
MIN_NOISE = 0.0005

REFRACTORY_S = 0.08

DRIFT_ACCUM_THRESHOLD = 0.002

BASE_NOTE = 60
NOTE_SPAN = 36

NOTE_LENGTH = 0.30
MIDI_CHANNEL = 0

SEND_CC = True
CC_NUM = 74
CC_RATE_HZ = 10.0


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def connect_to_puredata():
    try:
        result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
        plant_match = re.search(r'client (\d+).*Plant_MIDI', result.stdout)
        pd_match = re.search(r'client (\d+).*Pure Data', result.stdout)
        if plant_match and pd_match:
            plant_port = plant_match.group(1)
            pd_port = pd_match.group(1)
            subprocess.run(['aconnect', f'{plant_port}:0', f'{pd_port}:0'], check=True)
            print(f"✓ Connected Plant_MIDI ({plant_port}:0) → Pure Data ({pd_port}:0)")
            return True
        else:
            print("⚠ Couldn't find Pure Data MIDI port - is PureData running?")
            return False
    except Exception as e:
        print(f"⚠ Couldn't auto-connect MIDI: {e}")
        return False


def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c)
    ads.gain = ADS_GAIN
    chan = AnalogIn(ads, ads1x15.Pin.A0)

    midi_out = mido.open_output('Plant_MIDI', virtual=True)
    print("🌱 Plant MIDI port created")
    time.sleep(0.5)
    connect_to_puredata()

    dt = 1.0 / SAMPLE_HZ
    last_time = time.time()

    ema_v = chan.voltage
    prev_ema_v = ema_v
    ema_d = 0.0
    noise = 0.01

    drift_accum = 0.0
    last_trigger = 0.0

    last_cc = 0.0
    cc_dt = 1.0 / CC_RATE_HZ

    print("🌱 Plant MIDI (simple pre-random/threading) running — Ctrl+C to stop")

    while True:
        now = time.time()
        elapsed = now - last_time
        if elapsed < dt:
            time.sleep(dt - elapsed)
            now = time.time()
        last_time = now

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

        # Drift accumulation forces occasional events
        drift_accum += mag * dt
        force_event = False
        if drift_accum > DRIFT_ACCUM_THRESHOLD:
            drift_accum = 0.0
            force_event = True

        # Continuous CC
        if SEND_CC and (now - last_cc) > cc_dt:
            last_cc = now
            cc_val = int(clamp((ema_v / 3.3) * 127, 0, 127))
            try:
                midi_out.send(mido.Message("control_change", channel=MIDI_CHANNEL, control=CC_NUM, value=cc_val))
            except Exception:
                pass

        # Trigger note when magnitude exceeds adaptive threshold or drift forces
        if (mag > threshold or force_event) and (now - last_trigger) > REFRACTORY_S:
            last_trigger = now

            strength = 0.0
            if threshold > 0:
                strength = clamp((mag - threshold) / (threshold * 2.0), 0.0, 1.0)

            velocity = int(clamp(25 + int(strength * 102), 1, 127))

            pos = clamp(ema_v / 3.3, 0.0, 1.0)
            note_base = int(BASE_NOTE + (pos - 0.5) * 2 * NOTE_SPAN)
            note = int(clamp(note_base, 0, 127))

            try:
                midi_out.send(mido.Message("note_on", channel=MIDI_CHANNEL, note=note, velocity=velocity))
            except Exception:
                pass

            # Blocking hold; simple pre-threading behavior
            time.sleep(NOTE_LENGTH)

            try:
                midi_out.send(mido.Message("note_off", channel=MIDI_CHANNEL, note=note, velocity=0))
            except Exception:
                pass

            print(f"event v={ema_v:.3f} d={ema_d:+.5f} thr={threshold:.5f} note={note} vel={velocity} mag={mag:.6f}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped 🌿")