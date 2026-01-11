#!/bin/bash
set -e

# Vassal API Server Entrypoint
# Starts virtual display and runs Vassal with ArmadaBench extension
#
# Modes:
#   --mock       Run in mock mode (no Vassal, sample data)
#   --extension  Run Vassal with embedded extension (default)

echo "=== ArmadaBench Vassal Server ==="
echo "Module: ${VASSAL_MODULE_PATH:-/app/vassal-module/ArmadaModule.vmod}"
echo "Port: ${VASSAL_API_PORT:-8080}"

# Parse command line arguments
PORT=${VASSAL_API_PORT:-8080}
MODE="extension"
VNC_ENABLED="${ENABLE_VNC:-false}"

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --mock)
            MODE="mock"
            shift
            ;;
        --extension)
            MODE="extension"
            shift
            ;;
        --vnc)
            VNC_ENABLED="true"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

echo "Mode: $MODE"

# Start virtual display
echo "Starting Xvfb virtual display on :99..."
Xvfb :99 -screen 0 1920x1080x24 -ac &
XVFB_PID=$!
sleep 2

# Verify Xvfb is running
if ! kill -0 $XVFB_PID 2>/dev/null; then
    echo "ERROR: Failed to start Xvfb"
    exit 1
fi
echo "Xvfb started (PID: $XVFB_PID)"

# Optionally start VNC server for debugging
if [ "$VNC_ENABLED" = "true" ]; then
    echo "Starting VNC server on port 5900..."
    x11vnc -display :99 -forever -shared -rfbport 5900 -bg -nopw 2>/dev/null || true
    echo "VNC server started - connect to localhost:5900"
fi

# Cleanup function
cleanup() {
    echo "Shutting down..."
    if [ -n "$JAVA_PID" ]; then
        kill $JAVA_PID 2>/dev/null || true
    fi
    kill $XVFB_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGTERM SIGINT

# Start the server based on mode
echo ""

if [ "$MODE" = "mock" ]; then
    echo "=== Starting Mock API Server ==="
    # Use the standalone Java API in mock mode
    if [ -f "/app/vassal-api.jar" ]; then
        java -jar /app/vassal-api.jar --mock $PORT &
    else
        echo "ERROR: vassal-api.jar not found for mock mode"
        exit 1
    fi
    JAVA_PID=$!

elif [ "$MODE" = "extension" ]; then
    echo "=== Starting Vassal with ArmadaBench Extension ==="

    VASSAL_HOME="${VASSAL_HOME:-/app/vassal}"
    MODULE_PATH="${VASSAL_MODULE_PATH:-/app/vassal-module/ArmadaModule.vmod}"

    # Verify Vassal is installed
    if [ ! -d "$VASSAL_HOME" ]; then
        echo "ERROR: Vassal not found at $VASSAL_HOME"
        echo "Falling back to mock mode..."
        java -jar /app/vassal-api.jar --mock $PORT &
        JAVA_PID=$!
    else
        # The main Vassal JAR is Vengine.jar
        VASSAL_JAR="$VASSAL_HOME/lib/Vengine.jar"

        if [ ! -f "$VASSAL_JAR" ]; then
            echo "ERROR: Cannot find Vassal JAR at $VASSAL_JAR"
            ls -la "$VASSAL_HOME/lib" 2>/dev/null || true
            echo "Falling back to mock mode..."
            java -jar /app/vassal-api.jar --mock $PORT &
            JAVA_PID=$!
        else
            echo "Vassal JAR: $VASSAL_JAR"
            echo "Module: $MODULE_PATH"

            # Check if module exists
            if [ ! -f "$MODULE_PATH" ]; then
                echo "ERROR: Module not found at $MODULE_PATH"
                echo "Falling back to mock mode..."
                java -jar /app/vassal-api.jar --mock $PORT &
                JAVA_PID=$!
            else
                echo "Starting Vassal with module..."
                echo "Extension directory: /app/vassal-module/ArmadaModule_ext/"
                ls -la /app/vassal-module/ArmadaModule_ext/ 2>/dev/null || true

                # Add our extension JAR to the classpath so Vassal can find the classes
                EXTENSION_JAR="/app/extension/armadabench-extension.vmdx"

                # Run Vassal with the module using the official launch method
                # -Duser.dir must point to Vassal install dir for it to find its libs
                java \
                    -Darmadabench.port="$PORT" \
                    -Duser.dir="$VASSAL_HOME" \
                    -Duser.home="/root" \
                    -Djava.awt.headless=false \
                    -classpath "$VASSAL_JAR:$EXTENSION_JAR" \
                    VASSAL.launch.Player \
                    --load "$MODULE_PATH" 2>&1 &
                JAVA_PID=$!

                # Give Vassal time to start, then output any errors
                sleep 5
                echo "Vassal started, checking if process is running..."
                if kill -0 $JAVA_PID 2>/dev/null; then
                    echo "Vassal process is running"
                else
                    echo "ERROR: Vassal process exited early"
                    echo "Falling back to mock mode..."
                    java -jar /app/vassal-api.jar --mock $PORT &
                    JAVA_PID=$!
                fi
            fi
        fi
    fi
fi

echo "Server started (PID: $JAVA_PID)"

# Wait for server to be ready
echo "Waiting for API server to be ready..."
for i in {1..60}; do
    if curl -sf http://localhost:$PORT/api/health > /dev/null 2>&1; then
        echo ""
        echo "=== Server Ready ==="
        echo "API: http://localhost:$PORT"
        echo "Health: http://localhost:$PORT/api/health"
        echo "State: http://localhost:$PORT/api/state"
        if [ "$VNC_ENABLED" = "true" ]; then
            echo "VNC: localhost:5900"
        fi
        break
    fi
    echo -n "."
    sleep 1
done

# Check if server started successfully
if ! curl -sf http://localhost:$PORT/api/health > /dev/null 2>&1; then
    echo ""
    echo "WARNING: Server did not respond to health check within 60 seconds"
    echo "Check logs for errors. Server may still be starting..."
fi

# Keep container running and forward signals
wait $JAVA_PID
