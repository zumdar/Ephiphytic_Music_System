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
import subprocess
import re
import random
import threading


# =========================
# USER-TUNABLE PARAMETERS
# =========================

SAMPLE_HZ = 40.0

ADS_GAIN = 2                 # Increase to 4 if signal is very small
SMOOTH_ALPHA = 0.18          # Voltage smoothing
DERIV_ALPHA = 0.30           # Change-rate smoothing

NOISE_ALPHA = 0.02           # Noise floor learning rate
THRESHOLD_K = 0.5            # LOWER = more notes
MIN_NOISE = 0.0005

REFRACTORY_S = 0.08          # Minimum time between notes (internal micro-refractory)

# Slow drift accumulation (forces notes over time)
DRIFT_ACCUM_THRESHOLD = 0.002

BASE_NOTE = 60               # Center pitch (C4-ish)
NOTE_SPAN = 36               # ± semitones (3 octaves)

NOTE_LENGTH = 0.30
MIDI_CHANNEL = 0

SEND_CC = True
CC_NUM = 74                  # Brightness / timbre
CC_RATE_HZ = 10.0

# New tuning: require stronger/more "interesting" events
SIGN_CHANGE_REQUIRED = True      # require derivative sign change for peaks
THRESH_MULTIPLIER = 1.8         # require mag > threshold * multiplier to be interesting
PROB_BASE = 0.20                # base probability to actually send when interesting
PROB_SCALE = 0.6                # extra probability scaling with strength

# Additional gating to avoid floods: make interesting events more "spontaneous"
MIN_EVENT_INTERVAL = 3.0       # minimum seconds between distinct interesting events
EVENT_SUPPRESSION_MIN = 0.4    # minimum extra suppression after an event
EVENT_SUPPRESSION_SCALE = 2.5  # scales suppression inverse to strength
MAX_NOTES_PER_EVENT = 5        # usually send one note per event


# =========================
# HELPERS
# =========================

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def connect_to_puredata():
    """Auto-connect Plant_MIDI to Pure Data"""
    try:
        # Get MIDI connections
        result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
        
        # Find Plant_MIDI port
        plant_match = re.search(r'client (\d+).*Plant_MIDI', result.stdout)
        # Find Pure Data port
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
    midi_out = mido.open_output('Plant_MIDI', virtual=True)
    print("🌱 Plant MIDI port created")

    # Immediately clear any lingering sound: send All Sound Off (120) and All Notes Off (123) on all channels
    try:
        for ch in range(16):
            midi_out.send(mido.Message('control_change', channel=ch, control=120, value=0))  # All Sound Off
            midi_out.send(mido.Message('control_change', channel=ch, control=123, value=0))  # All Notes Off
    except Exception:
        pass

    time.sleep(0.5)  # Give port time to register
    connect_to_puredata()

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

    prev_raw_d = 0.0  # for sign-change detection

    last_event_time = 0.0  # strong global suppression between interesting events

    print("🌱 Plant MIDI ACTIVE mode running")
    print("INA333 → ADS1115 → RAW MIDI (interesting-change gating enabled)")
    print("Press Ctrl+C to stop")

    def schedule_note_off(note, delay):
        def off():
            try:
                midi_out.send(
                    mido.Message(
                        "note_off",
                        channel=MIDI_CHANNEL,
                        note=note,
                        velocity=0
                    )
                )
            except Exception:
                pass
        t = threading.Timer(delay, off)
        t.daemon = True
        t.start()

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
            try:
                midi_out.send(
                    mido.Message(
                        "control_change",
                        channel=MIDI_CHANNEL,
                        control=CC_NUM,
                        value=cc_val
                    )
                )
            except Exception:
                pass

        # Determine if this is an "interesting" change:
        sign_change = (raw_d * prev_raw_d) < 0
        prev_raw_d = raw_d

        is_strong = mag > (threshold * THRESH_MULTIPLIER)

        # If SIGN_CHANGE_REQUIRED, require a derivative sign change for a peak (helps avoid ramps)
        interesting = False
        if force_event:
            # force events should still respect the global event spacing to avoid floods
            interesting = True
        else:
            if SIGN_CHANGE_REQUIRED:
                interesting = is_strong and sign_change
            else:
                interesting = is_strong

        # Enforce a global minimum time between interesting events to avoid floods
        if interesting and (now - last_event_time) < MIN_EVENT_INTERVAL:
            interesting = False

        # Only trigger when interesting and past micro refractory
        if interesting and (now - last_trigger) > REFRACTORY_S:
            # strength relative to threshold
            strength = 0.0
            if threshold > 0:
                strength = clamp((mag - threshold) / (threshold * 2.0), 0.0, 1.0)

            # Probabilistic gating so output isn't grid-like
            send_chance = PROB_BASE + PROB_SCALE * strength
            if random.random() < send_chance or force_event:
                last_trigger = now

                # Calculate suppression time after this event:
                # stronger events slightly reduce suppression so they *can* be more spontaneous,
                # weaker events produce longer quiet periods
                suppression = EVENT_SUPPRESSION_MIN + (MIN_EVENT_INTERVAL * (1.0 - (strength * 0.9))) / EVENT_SUPPRESSION_SCALE
                last_event_time = now + suppression

                # usually send a single spontaneous note
                notes_to_send = 1
                for _ in range(notes_to_send):
                    # velocity from intensity
                    velocity = int(clamp(25 + strength * 102, 1, 127))

                    # pitch from absolute state with small random jitter
                    pos = clamp(ema_v / 3.3, 0.0, 1.0)
                    note_base = int(BASE_NOTE + (pos - 0.5) * 2 * NOTE_SPAN)
                    jitter = random.choice([-5, -3, -2, -1, 0, 1, 2, 3, 5]) if random.random() < 0.45 else 0
                    note = int(clamp(note_base + jitter, 0, 127))

                    # slight timing jitter before sending (small)
                    time.sleep(random.uniform(0.0, min(0.04, dt)))

                    try:
                        midi_out.send(
                            mido.Message(
                                "note_on",
                                channel=MIDI_CHANNEL,
                                note=note,
                                velocity=velocity
                            )
                        )
                    except Exception:
                        pass

                    # schedule note off non-blocking
                    length = NOTE_LENGTH * random.uniform(0.8, 1.2)
                    schedule_note_off(note, length)

                print(
                    f"event v={ema_v:.3f}V "
                    f"d={ema_d:+.5f} "
                    f"thr={threshold:.5f} "
                    f"note={note} vel={velocity} "
                    f"mag={mag:.6f} interesting={interesting} chance={send_chance:.2f} suppress={suppression:.2f}"
                )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped 🌿")