# 🎮 Auto Monster Project

[![Latest release](https://img.shields.io/github/v/release/some-guy250/AutoMonster?style=for-the-badge)](../../releases/latest)

A Python-based automation tool for Monster Legends, designed to handle repetitive tasks efficiently.

## 📚 Table of Contents

- [🎯 Introduction](#-introduction)
- [⚙️ Features](#-features)
- [💻 Installation](#-installation)
- [🔄 Updates](#-updates)
- [🕹️ Setting Up an Emulator](#-setting-up-an-emulator)
- [💬 Usage and Interface](#-usage-and-interface)
- [🚨 Disclaimer](#-disclaimer)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)

## 🎯 Introduction

The Auto Monster Project is a Python-based automation tool for the game Monster Legends. It is designed to handle
repetitive tasks within the game, such as playing ads, doing dungeons, etc. Please note that while the project is
functional, it is still in active development and may undergo changes and improvements.

**Compatibility:** The Auto Monster Project can be used on both phones and tablets via USB debugging, although it is primarily designed
for desktop use with emulators. Mobile device compatibility requires:
- USB debugging enabled in developer options
- Device resolution support (may require testing)

Note: Phone compatibility is still under development and not fully tested on all devices.

## ⚙️ Features

Current implementation status of major features:

✅ Fully Working:
- Monster-Wood ad automation
- Era Saga dungeon progression 
- Daily Resource Dungeons:
  - Gem Dungeon
  - Rune Dungeon
  - Maze Coin Dungeon
- Cavern Dungeons:
  - Ancestral Caverns (Evaris, Geneza, Jestin, etc.)
  - Era Caverns (Historia, Multiverse, etc.)
  - Automatic team management
  - Multi-dungeon automation
- PVP automation:
  - Auto battles
  - Box management
  - Box timer reduction
- Brightness controls for overnight runs

⚠️ Partially Working:
- Device connectivity:
  - Real device support (USB and wireless)

## 💻 Installation
Configure your emulator (see below)
### Quick Install (Recommended)
1. Download the [latest AutoMonster_Setup.exe](../../releases/latest)
2. Run the installer and follow the prompts 
3. Launch from Start Menu or desktop shortcut

### Manual Installation 
For developers or advanced users:
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run `python main.py`

## 🔄 Updates

The application includes an automatic update system that:
- Checks for updates on startup
- Downloads and installs new versions
- Preserves your settings
- Handles asset management

Updates are installed seamlessly without manual intervention.

## 🕹️ Device Setup

### Using an Emulator (Recommended)
- Resolution: 1280x720 (required)
- DPI: 240
- ADB enabled and accessible

### Recommended Emulators
1. **BlueStacks** (Recommended)
   - Best overall performance
   - Easy ADB setup
   - Stable with Monster Legends

2. **LDPlayer**
   - Good gaming performance
   - Lower resource usage
   - Simple configuration

### Setup Steps
1. Install your chosen emulator
2. Configure resolution and DPI settings
3. Enable ADB in emulator settings
4. Install Monster Legends APK (from APKPure recommended)
5. Test the game runs smoothly

### Using a Physical Device

#### USB Connection
1. Enable Developer Options:
   - Go to Settings > About Phone
   - Tap Build Number 7 times
   - Enter your device PIN if prompted

2. Enable USB Debugging:
   - Go to Settings > Developer Options
   - Enable USB Debugging
   - Enable "Stay Awake" (prevents screen timeout)

3. Connect Device:
   - Use a quality USB cable
   - Select "File Transfer" mode when prompted
   - Accept USB debugging prompt on device
   - Install device drivers if needed

#### Wireless Connection
1. First enable USB debugging as described above

2. Enable Wireless Debugging:
   - Keep device and computer on same network
   - Go to Developer Options > Wireless Debugging
   - Enable Wireless Debugging
   - Tap "Pair device with pairing code"
   - Note the IP address and port (e.g., 192.168.1.100:5555)

3. Connect Device:
   - Launch AutoMonster
   - Enter the IP address and port in wireless connection field
   - Click "Connect Wireless"
   - Accept the debugging prompt on device

4. Test Connection:
   - Verify preview window shows your device screen
   - Check connection status in log window
   - Ensure stable network connection for reliability

### Device Selection Interface
When you first launch AutoMonster, you'll see the device selection screen:
- Lists all available devices (emulators and phones)
- Shows connection status and resolution
- Allows testing connection before proceeding
- Remembers last used device

## 💬 Usage and Interface

### Device Connection
1. Launch AutoMonster
2. Connect your device via USB or wireless

### Main Interface Layout
The interface consists of three main panels:

#### Left Panel - Command Controls
- **Command Selection**: Dropdown menu to choose automation task
- **Task Parameters**: Configurable settings for each command
- **Control Buttons**: 
  - Start: Begin automation
  - Stop: Halt current task
  - Save Settings: Store current parameters as defaults

#### Center Panel - Preview
- Live preview of your device screen
- Brightness controls:
  - Lower Brightness: Reduce screen brightness
  - Reset Brightness: Return to auto brightness

#### Right Panel - Information
- Detailed descriptions of selected commands
- Parameter explanations
- Tips and requirements


### Tips for Usage
- Monitor the log window for status updates and errors
- Use the preview window to verify automation is working correctly
- For overnight runs, consider using brightness controls

### Troubleshooting
- If automation seems stuck, check the log window for errors
- Use the Stop button to halt current operations
- Refresh device connection if preview becomes unresponsive

## 🚨 Disclaimer 

This tool is for educational purposes. Usage may violate Monster Legends' terms of service. Use at your own risk and responsibility.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

### 🐛 Bug Reports
Found a bug? You can:
- Message me on Reddit: [@some-guy250](https://reddit.com/user/some-guy250)
- Open an issue on GitHub

## 📜 License

Licensed under MIT License - see LICENSE file for details.

