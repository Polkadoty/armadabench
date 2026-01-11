#!/bin/bash
# Vassal Launcher Script
# Launches Vassal Player with the Armada module and ArmadaBench extension

set -e

VASSAL_HOME="${VASSAL_HOME:-/app/vassal}"
MODULE_PATH="${VASSAL_MODULE_PATH:-/app/vassal-module/ArmadaModule.vmod}"
EXTENSION_PATH="${EXTENSION_PATH:-/app/extension/armadabench-extension.vmdx}"
PORT="${VASSAL_API_PORT:-8080}"

echo "=== Vassal Launcher ==="
echo "Vassal Home: $VASSAL_HOME"
echo "Module: $MODULE_PATH"
echo "Extension: $EXTENSION_PATH"
echo "API Port: $PORT"

# Verify files exist
if [ ! -d "$VASSAL_HOME" ]; then
    echo "ERROR: Vassal not found at $VASSAL_HOME"
    exit 1
fi

if [ ! -f "$MODULE_PATH" ]; then
    echo "ERROR: Module not found at $MODULE_PATH"
    exit 1
fi

if [ ! -f "$EXTENSION_PATH" ]; then
    echo "ERROR: Extension not found at $EXTENSION_PATH"
    exit 1
fi

# Create the extension directory for the module
# Vassal looks for extensions in <module_dir>/<module_name>_ext/
MODULE_DIR=$(dirname "$MODULE_PATH")
MODULE_NAME=$(basename "$MODULE_PATH" .vmod)
EXT_DIR="${MODULE_DIR}/${MODULE_NAME}_ext"

echo "Setting up extension directory: $EXT_DIR"
mkdir -p "$EXT_DIR"
cp "$EXTENSION_PATH" "$EXT_DIR/"

# Also set up user preferences directory for extensions
# Vassal also looks in ~/.VASSAL/
VASSAL_PREFS_DIR="${HOME}/.VASSAL"
mkdir -p "$VASSAL_PREFS_DIR"

# Find the Vassal JAR
VASSAL_JAR="${VASSAL_HOME}/lib/Vassal.jar"
if [ ! -f "$VASSAL_JAR" ]; then
    # Try alternate location
    VASSAL_JAR=$(find "$VASSAL_HOME" -name "Vassal.jar" -o -name "vassal-app*.jar" 2>/dev/null | head -1)
fi

if [ -z "$VASSAL_JAR" ] || [ ! -f "$VASSAL_JAR" ]; then
    echo "ERROR: Cannot find Vassal JAR in $VASSAL_HOME"
    ls -la "$VASSAL_HOME"
    exit 1
fi

echo "Using Vassal JAR: $VASSAL_JAR"

# Build the classpath - include all JARs in Vassal lib directory
CLASSPATH="$VASSAL_JAR"
if [ -d "${VASSAL_HOME}/lib" ]; then
    for jar in "${VASSAL_HOME}/lib"/*.jar; do
        if [ -f "$jar" ] && [ "$jar" != "$VASSAL_JAR" ]; then
            CLASSPATH="${CLASSPATH}:${jar}"
        fi
    done
fi

echo "Starting Vassal Player..."

# Set system properties for our extension
# -Darmadabench.port sets the API server port
# Run Vassal Player with the module
exec java \
    -Darmadabench.port="$PORT" \
    -Duser.home="$HOME" \
    -Djava.awt.headless=false \
    -cp "$CLASSPATH" \
    VASSAL.launch.Player \
    --load "$MODULE_PATH"
