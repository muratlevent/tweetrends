#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 X (Twitter) Global Trending Scraper - Setup & Run${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "❌ Error: python3 is not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}🔗 Activating virtual environment...${NC}"
source venv/bin/activate

# Install requirements
echo -e "${BLUE}📥 Installing dependencies...${NC}"
pip install -r requirements.txt -q

# Install Playwright browsers (chromium)
echo -e "${BLUE}🌐 Installing Playwright browsers...${NC}"
playwright install chromium

# Run the scraper
echo -e "${GREEN}✨ Starting the scraper...${NC}"
python3 scraper.py "$@"

echo -e "${GREEN}✅ Done! Check trends.json for results.${NC}"
