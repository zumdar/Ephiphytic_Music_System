import fluidsynth
import time

# Initialize FluidSynth
fs = fluidsynth.Synth()
fs.start(driver="alsa")

# Load the soundfont (use the correct path)
sfid = fs.sfload("/usr/share/sounds/sf2/default-GM.sf2")
fs.program_select(0, sfid, 0, 0)  # Channel 0, bank 0, preset 0 (Piano)

# Play a test note
print("Playing Middle C...")
fs.noteon(0, 60, 100)  # Channel 0, Middle C, velocity 100
time.sleep(1)
fs.noteoff(0, 60)

print("Playing a chord...")
fs.noteon(0, 60, 100)  # C
fs.noteon(0, 64, 100)  # E
fs.noteon(0, 67, 100)  # G
time.sleep(2)
fs.noteoff(0, 60)
fs.noteoff(0, 64)
fs.noteoff(0, 67)

time.sleep(0.5)
fs.delete()
print("FluidSynth test complete!")