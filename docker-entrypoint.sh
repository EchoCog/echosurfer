#!/bin/bash

# Start Xvfb
Xvfb :99 -screen 0 1920x1080x24 &

# Wait for Xvfb to start
sleep 2

# Start VNC server
x11vnc -display :99 -nopw -forever -xkb &

# Keep container running
tail -f /dev/null
