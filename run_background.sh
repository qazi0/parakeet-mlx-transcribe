#!/bin/bash
#
# Background launcher for live_stt.py
# This script runs the STT application in the background without console output
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="$SCRIPT_DIR/stt_output.log"
PID_FILE="$SCRIPT_DIR/stt.pid"

# Function to start the service
start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "STT service is already running (PID: $PID)"
            return 1
        else
            rm "$PID_FILE"
        fi
    fi

    echo "Starting STT service in background..."
    cd "$SCRIPT_DIR"

    # Activate virtual environment and run in background
    source .venv/bin/activate

    # Run in background, redirect output to log
    nohup python live_stt.py > "$LOG_FILE" 2>&1 &

    echo $! > "$PID_FILE"
    echo "STT service started (PID: $(cat $PID_FILE))"
    echo "Log file: $LOG_FILE"
    echo "To stop: ./run_background.sh stop"
}

# Function to stop the service
stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "STT service is not running"
        return 1
    fi

    PID=$(cat "$PID_FILE")
    echo "Stopping STT service (PID: $PID)..."

    if kill $PID 2>/dev/null; then
        rm "$PID_FILE"
        echo "STT service stopped"
    else
        echo "Failed to stop service (process may have already exited)"
        rm "$PID_FILE"
    fi
}

# Function to check status
status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "STT service is running (PID: $PID)"
            return 0
        else
            echo "STT service is not running (stale PID file)"
            return 1
        fi
    else
        echo "STT service is not running"
        return 1
    fi
}

# Function to show logs
logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "No log file found"
    fi
}

# Main script
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 1
        start
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start STT service in background"
        echo "  stop     - Stop STT service"
        echo "  restart  - Restart STT service"
        echo "  status   - Check if service is running"
        echo "  logs     - Show service logs (tail -f)"
        exit 1
        ;;
esac
