#!/bin/bash
echo "🔱 APEX UPLINK: ESTABLISHING SOVEREIGN BRIDGE..."
# This opens the port for the mobile agent to communicate with the Debian root
# Replace <PORT> with your preferred secure port (e.g., 8080)
python3 -m http.server 8080 --directory ./deliveries &
echo "📡 Bridge Active. Waiting for APK Handshake on Port 8080."
