#!/bin/bash
# Stop the llama-server running on port 8080

PID=$(netstat -ano 2>/dev/null | grep ":8080.*LISTENING" | awk '{print $5}' | head -1)

if [ -z "$PID" ]; then
    echo "No llama-server found on port 8080"
    exit 0
fi

echo "Stopping llama-server (PID: $PID) on port 8080..."
taskkill //PID "$PID" //F 2>/dev/null

if [ $? -eq 0 ]; then
    echo "Server stopped."
else
    echo "Failed to stop server. Try: taskkill //PID $PID //F"
fi
