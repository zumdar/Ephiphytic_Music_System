# Scripts and Services

These need to run! The services run at boot. The services run the scripts. 
IF you need to run the scrips, they can be run by just typing
`~/start_puredata.sh` they do not need the full path!

This Pure data script runs: Plant_Synth_dp_2.pd located in 
/home/patch/Desktop/EMS_Plant_Music/PD/Pd_for_Daniel_2026

Pure Data script:       /home/patch/start_puredata.sh
Pure Data Service:      ~/.config/systemd/user/puredata.service

Plant MIDI script:      /home/patch/start_plant_midi_gui.sh
Plant MIDI service:     ~/.config/systemd/user/plant-midi-monitor.service

MIDI Connect Script:    /home/patch/connect_midi.sh
MIDI Connect service:   /etc/systemd/system/midi-connect.service

Prestream audio audition script: ~/start_prestream_audio.sh 

Streaming script: Live_Streaming/live_stream_3rd.sh