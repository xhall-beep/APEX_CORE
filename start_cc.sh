#!/bin/bash
echo "🔱 IGNITING SOVEREIGN CORE V85.2..."
# Kill any ghost processes
pkill -f control_api.py
pkill -f cloudflared

# Start the Watchdog in the background
nohup python3 watchdog.py > watchdog.log 2>&1 &
echo "🔱 WATCHDOG DEPLOYED. SYSTEM IS NOW IMMORTAL."
