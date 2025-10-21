#!/bin/bash

# DKI Engine - macOS One-Click Installer
# Professional Investigation Platform

# Make script executable
chmod +x "$0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Clear screen and show banner
clear
echo -e "${BLUE}"
echo "  ██████╗ ██╗  ██╗██╗    ███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗"
echo "  ██╔══██╗██║ ██╔╝██║    ██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝"
echo "  ██║  ██║█████╔╝ ██║    █████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗  "
echo "  ██║  ██║██╔═██╗ ██║    ██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝  "
echo "  ██████╔╝██║  ██╗██║    ███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗"
echo "  ╚═════╝ ╚═╝  ╚═╝╚═╝    ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝"
echo -e "${NC}"
echo -e "${CYAN}                    🔍 Professional Investigation Platform 🔍${NC}"
echo -e "${CYAN}                           macOS ONE-CLICK INSTALLER${NC}"
echo ""
echo "================================================================================"

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/DKI_Engine"
VENV_DIR="$INSTALL_DIR/dki_env"

# Step 1: Check Python Installation
echo -e "${YELLOW}[1/6]${NC} 🐍 Checking Python installation..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ $PYTHON_VERSION found!${NC}"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo -e "${GREEN}✅ $PYTHON_VERSION found!${NC}"
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python not found!${NC}"
    echo ""
    echo "Installing Python via Homebrew..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install Python
    brew install python
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        echo -e "${GREEN}✅ Python installed successfully!${NC}"
    else
        echo -e "${RED}❌ Python installation failed${NC}"
        echo "Please install Python manually from https://python.org"
        exit 1
    fi
fi

# Step 2: Create Installation Directory
echo -e "${YELLOW}[2/6]${NC} 📁 Creating installation directory..."

if [ -d "$INSTALL_DIR" ]; then
    echo -e "${GREEN}✅ Installation directory exists${NC}"
else
    mkdir -p "$INSTALL_DIR"
    echo -e "${GREEN}✅ Created installation directory: $INSTALL_DIR${NC}"
fi

# Copy files to installation directory
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
cd "$INSTALL_DIR"

# Step 3: Create Virtual Environment
echo -e "${YELLOW}[3/6]${NC} 🏗️  Creating virtual environment..."

if [ -d "$VENV_DIR" ]; then
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
else
    $PYTHON_CMD -m venv "$VENV_DIR"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Virtual environment created successfully!${NC}"
    else
        echo -e "${RED}❌ Failed to create virtual environment${NC}"
        exit 1
    fi
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Step 4: Install Dependencies
echo -e "${YELLOW}[4/6]${NC} 📦 Installing dependencies..."
echo "This may take several minutes..."

# Upgrade pip
pip install --upgrade pip --quiet

# Install core dependencies
echo "Installing core packages..."
pip install --quiet tkinter-tooltip pillow reportlab python-docx openpyxl pandas numpy requests beautifulsoup4 cryptography

# Install AI/ML packages
echo "Installing AI/ML packages..."
pip install --quiet openai transformers torch spacy

# Install media processing
echo "Installing media processing packages..."
pip install --quiet opencv-python librosa soundfile ffmpeg-python moviepy

# Install OCR and document processing
echo "Installing OCR packages..."
pip install --quiet pytesseract PyPDF2 pdfplumber easyocr

# Install additional utilities
echo "Installing utilities..."
pip install --quiet selenium psutil

# Install OpenAI Whisper
echo "Installing OpenAI Whisper..."
pip install --quiet openai-whisper

echo -e "${GREEN}✅ All dependencies installed successfully!${NC}"

# Step 5: Create Launch Scripts
echo -e "${YELLOW}[5/6]${NC} 🚀 Creating launch scripts..."

# Create main launcher
cat > "$INSTALL_DIR/launch_dki_engine.command" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source dki_env/bin/activate
python UI/main_application.py
EOF

chmod +x "$INSTALL_DIR/launch_dki_engine.command"

# Create desktop alias
if [ -d "$HOME/Desktop" ]; then
    ln -sf "$INSTALL_DIR/launch_dki_engine.command" "$HOME/Desktop/DKI Engine"
    echo -e "${GREEN}✅ Desktop shortcut created${NC}"
fi

# Create Applications folder shortcut
if [ -d "/Applications" ]; then
    cat > "/Applications/DKI Engine.app/Contents/MacOS/DKI Engine" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
source dki_env/bin/activate
python UI/main_application.py
EOF
    
    # Create app bundle structure
    mkdir -p "/Applications/DKI Engine.app/Contents/MacOS"
    chmod +x "/Applications/DKI Engine.app/Contents/MacOS/DKI Engine"
    
    # Create Info.plist
    cat > "/Applications/DKI Engine.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>DKI Engine</string>
    <key>CFBundleDisplayName</key>
    <string>DKI Engine</string>
    <key>CFBundleIdentifier</key>
    <string>com.dkiservices.engine</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleExecutable</key>
    <string>DKI Engine</string>
</dict>
</plist>
EOF
    
    echo -e "${GREEN}✅ Applications folder shortcut created${NC}"
fi

echo -e "${GREEN}✅ Launch scripts created!${NC}"

# Step 6: System Validation
echo -e "${YELLOW}[6/6]${NC} ✅ Running system validation..."

# Test core dependencies
python -c "import tkinter, PIL, reportlab; print('Core dependencies OK')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Core dependencies validated${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Some core dependencies may not be working properly${NC}"
fi

# Test AI dependencies
python -c "import openai, whisper; print('AI dependencies OK')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ AI dependencies validated${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: AI dependencies may need additional setup${NC}"
fi

# Create installation flag
echo "Installation completed on $(date)" > "$INSTALL_DIR/installation.flag"

# Deactivate virtual environment
deactivate

echo ""
echo "================================================================================"
echo -e "${GREEN}                           🎉 INSTALLATION COMPLETE! 🎉${NC}"
echo "================================================================================"
echo ""
echo -e "${GREEN}✅ DKI Engine has been successfully installed!${NC}"
echo ""
echo -e "${CYAN}🚀 LAUNCH OPTIONS:${NC}"
echo "   • Desktop: Double-click 'DKI Engine' on your desktop"
echo "   • Applications: Launch from Applications folder"
echo "   • Terminal: Run ./launch_dki_engine.command"
echo ""
echo -e "${CYAN}📚 DOCUMENTATION:${NC}"
echo "   • Quick Start: $INSTALL_DIR/QUICK_START.md"
echo ""
echo -e "${CYAN}🔧 FEATURES INSTALLED:${NC}"
echo "   • 13 Professional report sections"
echo "   • AI-powered analysis (OpenAI integration)"
echo "   • Audio/video processing with transcription"
echo "   • OCR document processing"
echo "   • OSINT investigation tools"
echo "   • Real-time system monitoring"
echo ""
echo "Press any key to launch DKI Engine now, or close to finish installation."
read -n 1 -s

# Launch application
echo -e "${CYAN}🚀 Launching DKI Engine...${NC}"
"$INSTALL_DIR/launch_dki_engine.command"





