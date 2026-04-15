#!/bin/bash
#
# Nexus Agentic OS - Setup Script
# One-command installation for macOS and Linux
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Nexus Agentic OS - Setup${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo -e "${GREEN}✓ Python $python_version detected${NC}"
else
    echo -e "${RED}✗ Python 3.9+ required, found $python_version${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Make binaries executable
echo -e "${YELLOW}Setting up binaries...${NC}"
chmod +x bin/*
find skills -name "bin" -type d -exec chmod -R +x {}/ \; 2>/dev/null || true

# Create user profile from template if it doesn't exist
if [ ! -f "knowledge/user_profile.json" ]; then
    echo -e "${YELLOW}Creating user profile...${NC}"
    cp knowledge/user_profile.template.json knowledge/user_profile.json
fi

# Generate tools manifest
echo -e "${YELLOW}Generating tools manifest...${NC}"
python3 scripts/generate_tools_manifest.py 2>/dev/null || echo "Note: generate_tools_manifest.py not found, skipping"

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "To get started:"
echo "  1. Activate the virtual environment: source .venv/bin/activate"
echo "  2. Run the MCP server: python3 bin/mcp_server.py"
echo "  3. Read the documentation: cat README.md"
echo ""
echo "Optional dependencies:"
echo "  - Install Node.js tools: npm install -g bb-browser defuddle"
echo "  - Set up Tavily API key: export TAVILY_API_KEY=your_key"
echo ""
