# DKI Engine - Quick Start Guide

## Launch Instructions

### Windows

#### Option 1: Start Menu Launch (Recommended)
1. Open F:\Start Menu.
2. Double-click DKI_ENGINE_LAUNCHER.bat (runs dependency checks every time).
3. Daily use: launch the same file or START_HERE.bat in that folder.

#### Option 2: Desktop Shortcut
1. Run F:\Start Menu\INSTALL_DKI_ENGINE.bat as Administrator.
2. Double-click the new DKI Engine shortcut on the desktop.
3. The shortcut targets F:\Start Menu\START_HERE.bat and starts the app.

#### Option 3: Windows Start Menu
1. After installing, press the Windows key and type DKI Engine.
2. Launch the entry under *Apps ? DKI Engine* (points to the Start Menu launcher).
3. Use this entry for everyday sessions.

### macOS
1. Run F:\DKI_Engine_Installer_macOS.command to set up the environment.
2. Use the generated launch_dki_engine.command (also copied to the Desktop).
3. Drag that command file to the Dock for one-click access.

## First Launch
- Setup wizard prompts for API keys if required.
- Confirm investigator profile information.
- Control panel loads with status indicators when ready.

## Main Interface Highlights
- File drop zone for drag-and-drop ingestion.
- Case management control panel.
- Premium options: printing, signatures, watermarks.
- Report generator covering all investigation sections.

## System Requirements

### Minimum
- Windows 10+/macOS 10.14+/Linux
- Python 3.8+
- 4?GB RAM (8?GB recommended)
- 2?GB free disk space
- Internet connection for OSINT features

### Recommended
- Windows 11/macOS 12+
- Python 3.10+
- 16?GB RAM for large cases
- 10?GB free disk space
- Dedicated GPU for intensive media work

## Troubleshooting

### ?Python not found?
1. Install Python from https://python.org.
2. Enable ?Add Python to PATH? during installation.
3. Reboot, then rerun INSTALL_DKI_ENGINE.bat.

### ?Dependencies failed?
1. Rerun INSTALL_DKI_ENGINE.bat as Administrator.
2. Check network connectivity.
3. Upgrade pip manually: python -m pip install --upgrade pip.

### ?Application won?t start?
1. Delete F:\Report Engine\DKI_Repository\user_profiles.db (forces fresh setup).
2. Launch F:\Start Menu\DKI_ENGINE_LAUNCHER.bat.
3. Complete the setup wizard again.

### ?UI looks broken?
1. Update display drivers.
2. Ensure resolution is at least 1280?720.
3. Try Windows compatibility mode (Windows 8).

## Support
- Restart: close all windows and relaunch from the Start Menu.
- Clean install: rerun INSTALL_DKI_ENGINE.bat to rebuild the environment.
- Update dependencies: run pip install --upgrade -r requirements.txt inside %BASE_DRIVE%\dki_env.
- Documentation: F:\Report Engine\SOP_DKI_Engine.md.
- Technical blueprint: F:\Report Engine\BUILD_BLUEPRINT.md.
- Training material: F:\Report Engine\PRD_DKI_Engine.md.

## You?re Ready
DKI Engine is prepared to ingest multi-format evidence, assemble full reports, run OSINT verification, apply signatures, and maintain complete audit trails.

Enjoy the platform.
