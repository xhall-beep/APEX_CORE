#!/bin/bash
echo "🔱 IGNITING SOVEREIGN MULTI-BRIDGE..."
# Starting the Control API in the background
./start_cc.sh &
sleep 5
# Establishing the Global Tunnel
cloudflared tunnel --url http://localhost:8080
