#!/bin/bash
set -e

# ArmadaBench Runner Entrypoint
# Handles startup, virtual display, and benchmark execution

echo "=== ArmadaBench Runner ==="
echo "Run ID: ${RUN_ID:-not-set}"
echo "Output Dir: ${ARMADABENCH_OUTPUT_DIR}"

# Start virtual display if not already running
if [ -z "$SKIP_XVFB" ] && ! pgrep -x "Xvfb" > /dev/null; then
    echo "Starting virtual display..."
    Xvfb :99 -screen 0 1920x1080x24 &
    sleep 2
fi

# Optionally start VNC server for debugging
if [ "$ENABLE_VNC" = "true" ]; then
    echo "Starting VNC server on port 5900..."
    x11vnc -display :99 -forever -shared -rfbport 5900 -bg
fi

# Execute command
case "$1" in
    run)
        echo "Starting benchmark run..."
        shift
        exec python -m armadabench_mcp.runner "$@"
        ;;
    server)
        echo "Starting MCP server..."
        shift
        exec python -m armadabench_mcp.server "$@"
        ;;
    test)
        echo "Running tests..."
        shift
        exec pytest "$@"
        ;;
    shell)
        echo "Starting shell..."
        exec /bin/bash
        ;;
    *)
        echo "Unknown command: $1"
        echo "Usage: entrypoint.sh {run|server|test|shell}"
        exit 1
        ;;
esac
