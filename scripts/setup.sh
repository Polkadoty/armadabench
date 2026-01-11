#!/bin/bash
# ArmadaBench Setup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🎯 ArmadaBench Setup"
echo "===================="
echo ""

# Check for Java
echo "Checking prerequisites..."

if ! command -v java &> /dev/null; then
    echo "❌ Java not found. Please install Java 17+:"
    echo "   brew install --cask temurin@17"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | head -1 | cut -d'"' -f2 | cut -d'.' -f1)
if [ "$JAVA_VERSION" -lt 17 ]; then
    echo "❌ Java 17+ required, found version $JAVA_VERSION"
    exit 1
fi
echo "✅ Java $JAVA_VERSION found"

# Check for Maven
if ! command -v mvn &> /dev/null; then
    echo "❌ Maven not found. Please install:"
    echo "   brew install maven"
    exit 1
fi
echo "✅ Maven found"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Python $PYTHON_VERSION found"

echo ""
echo "Setting up components..."
echo ""

# Install Python MCP server
echo "📦 Installing Python MCP server..."
cd "$PROJECT_DIR/mcp-server"
pip install -e . --quiet
echo "✅ MCP server installed"

# Check for Vassal source
VASSAL_DIR="$PROJECT_DIR/../vassal"
if [ -d "$VASSAL_DIR" ]; then
    echo ""
    echo "📦 Building Vassal (this may take a few minutes)..."
    cd "$VASSAL_DIR"
    mvn install -DskipTests -q
    echo "✅ Vassal built and installed to local Maven repo"

    # Build Vassal integration
    echo ""
    echo "📦 Building Vassal integration..."
    cd "$PROJECT_DIR/vassal-integration"
    mvn clean package -q
    echo "✅ Vassal integration built"
else
    echo ""
    echo "⚠️  Vassal source not found at $VASSAL_DIR"
    echo "   Vassal integration build skipped."
    echo "   Clone Vassal from https://github.com/vassalengine/vassal"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start ArmadaBench:"
echo ""
echo "1. Start the Vassal API server:"
echo "   cd vassal-integration"
echo "   java -jar target/vassal-integration-0.1.0-SNAPSHOT.jar /path/to/ArmadaModule.vmod"
echo ""
echo "2. In another terminal, run the MCP server:"
echo "   armadabench-mcp"
echo ""
echo "3. Or configure Claude Desktop to use the MCP server"
echo ""
