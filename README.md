# AutoMonster

Automation tool for [Monster Legends](https://www.igg.com/en/game/monster-legends) using ADB and OpenCV template matching.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Latest Release](https://img.shields.io/github/v/release/some-guy250/AutoMonster?style=flat-square)](../../releases/latest)

## Features

- **Ads:** Watch all available Monster Wood ads for rewards
- **Reduce Time:** Watch ads to reduce in-game timers
- **Resource Dungeons:** Auto-complete Gem, Rune, and Maze Coin dungeons with optional stamina wait
- **Cavern Dungeons:** Run Ancestral (9) and Era (14) caverns with automatic team management
- **Era Saga:** Auto-progress through the currently selected Era Saga
- **PVP:** Auto-battle with box management and timer reduction
- **Breed Monsters:** Breed with Mountain/Tree selection, optional feed and sell
- **Feed & Sell Monsters:** Level up and sell unwanted monsters
- **Craft Runes:** Craft runes (levels I–V, all types) for single or team monsters
- **Close Game:** Exit the game, the app, or shut down the PC
- **Macro System:** Chain commands into automated sequences
- **Brightness Controls:** Lower screen brightness for overnight runs
- **Automatic Updates:** Checks for and installs updates on startup

## Installation

### Quick Install (Recommended)

1. Download the latest `AutoMonster_Setup.exe` from [releases](../../releases/latest)
2. Run the installer and follow the prompts
3. Launch from Start Menu or desktop shortcut

### Manual Installation

For developers or advanced users:

```bash
python -m pip install --upgrade pip
pip install av==16.0.1 --only-binary=:all:
pip install --no-deps -r requirements-scrcpy.txt
pip install -r requirements.txt
python main.py
```

## Device Setup

### Emulator (Recommended)

- **Resolution:** 1280x720 (required)
- **DPI:** 240
- **ADB:** Enabled and accessible

Recommended emulators: [BlueStacks](https://www.bluestacks.com) (best performance), [LDPlayer](https://ldplayer.net) (lower resource usage).

### Physical Device

1. Enable **Developer Options** (Settings > About Phone > tap Build Number 7 times)
2. Enable **USB Debugging** and **Stay Awake** in Developer Options
3. Connect via USB (device appears in the dropdown automatically) or enable **Wireless Debugging** and enter the IP address and port manually

## Usage

### Commands

Select a command from the dropdown, configure its parameters, and click **Save Settings** to store defaults.

### Macro System

Chain commands into automated sequences via **Macro Manager**:

1. Create a new macro and name it
2. Add steps by selecting commands and configuring parameters
3. Reorder steps with arrow buttons
4. Enable **Lower Brightness** and / or **Lock Device** for overnight runs

### Troubleshooting

- Check the log window for status updates and errors
- Use **Stop** to halt any running operation

## Requirements

- Windows (installer), macOS or Linux (manual)
- Python 3.10+
- ADB-capable device or emulator
- Monster Legends at 1280x720 resolution

## Bug Reports

- [Open an issue on GitHub](../../issues)
- Message me on Reddit: [@some-guy250](https://reddit.com/user/some-guy250)

## Disclaimer

This tool is for educational purposes. Usage may violate Monster Legends' terms of service. Use at your own risk.

## License

MIT. See [LICENSE](LICENSE).
