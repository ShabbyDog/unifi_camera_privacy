#!/bin/bash
# Setup script for UniFi Protect Privacy Button Controller on Raspberry Pi

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}UniFi Privacy Button Setup${NC}"
echo -e "${BLUE}================================${NC}"

# Check if running on Raspberry Pi
if ! cat /proc/cpuinfo | grep -q "Raspberry Pi"; then
    echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi${NC}"
    echo -e "${YELLOW}GPIO functionality may not work correctly${NC}"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root${NC}"
   echo -e "${YELLOW}Please run as your regular user${NC}"
   exit 1
fi

# Update system
echo -e "${BLUE}Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo -e "${BLUE}Installing system dependencies...${NC}"
sudo apt install -y python3 python3-pip python3-venv git

# Add user to gpio group
echo -e "${BLUE}Adding user to gpio group...${NC}"
sudo usermod -a -G gpio $USER

# Create system directory for the service
SYSTEM_DIR="/opt/unifi-camera-privacy"
echo -e "${BLUE}Creating system directory: $SYSTEM_DIR${NC}"
sudo mkdir -p "$SYSTEM_DIR"

# Copy application files to system directory
echo -e "${BLUE}Copying application files...${NC}"
sudo cp -r ./* "$SYSTEM_DIR/"

# Set proper ownership and permissions
echo -e "${BLUE}Setting permissions...${NC}"
sudo chown -R $USER:gpio "$SYSTEM_DIR"
sudo chmod -R 755 "$SYSTEM_DIR"

cd "$SYSTEM_DIR"

# Create virtual environment in system directory
echo -e "${BLUE}Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Copy UFP config if it exists
if [ -d "/home/$USER/.config/ufp" ]; then
    echo -e "${BLUE}Copying UniFi Protect configuration...${NC}"
    mkdir -p .config/ufp
    cp /home/$USER/.config/ufp/* .config/ufp/
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo -e "${YELLOW}Please create .env file with your UniFi Protect settings${NC}"
    echo -e "${BLUE}Example:${NC}"
    cat config.env.example
    echo
    read -p "Press Enter to continue..."
fi

# Test the connection (optional)
echo -e "${BLUE}Testing UniFi Protect connection...${NC}"
if ./venv/bin/python test_connection.py; then
    echo -e "${GREEN}✓ Connection test successful${NC}"
else
    echo -e "${YELLOW}⚠ Connection test failed - please check your .env configuration${NC}"
fi

# Install systemd service
echo -e "${BLUE}Installing systemd service...${NC}"
sudo cp privacy-button.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable privacy-button.service

echo
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo
echo -e "${BLUE}Hardware Setup:${NC}"
echo -e "  1. Connect a button between GPIO 18 (Pin 12) and Ground (Pin 14)"
echo -e "  2. (Optional) Connect an LED between GPIO 24 (Pin 18) and Ground (Pin 20) with 220Ω resistor"
echo -e "  3. See HARDWARE_SETUP.md for detailed wiring diagrams"
echo
echo -e "${BLUE}Configuration:${NC}"
echo -e "  • Camera name: ${YELLOW}Soverom${NC}"
echo -e "  • Button pin: ${YELLOW}GPIO 18${NC}"
echo -e "  • LED pin: ${YELLOW}GPIO 24${NC}"
echo -e "  • Timeout: ${YELLOW}60 minutes${NC}"
echo -e "  • Application location: ${YELLOW}$SYSTEM_DIR${NC}"
echo
echo -e "${BLUE}To customize settings, edit:${NC}"
echo -e "  ${SYSTEM_DIR}/gpio_privacy_controller.py"
echo -e "  Look for the configuration section in main()"
echo
echo -e "${BLUE}Service Management:${NC}"
echo -e "  Start service:   ${YELLOW}sudo systemctl start privacy-button${NC}"
echo -e "  Stop service:    ${YELLOW}sudo systemctl stop privacy-button${NC}"
echo -e "  Check status:    ${YELLOW}sudo systemctl status privacy-button${NC}"
echo -e "  View logs:       ${YELLOW}sudo journalctl -u privacy-button -f${NC}"
echo
echo -e "${BLUE}Manual Testing:${NC}"
echo -e "  Test GPIO:       ${YELLOW}cd $SYSTEM_DIR && ./venv/bin/python test_gpio.py${NC}"
echo -e "  Run manually:    ${YELLOW}cd $SYSTEM_DIR && ./venv/bin/python gpio_privacy_controller.py${NC}"
echo
echo -e "${YELLOW}Note: You may need to log out and log back in for group changes to take effect${NC}"
echo
read -p "Start the privacy button service now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Starting privacy button service...${NC}"
    sudo systemctl start privacy-button.service
    sleep 2
    sudo systemctl status privacy-button.service
fi 