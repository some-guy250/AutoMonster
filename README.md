# 🎮 Auto Monster Project

[![Latest release](https://img.shields.io/github/v/release/some-guy250/AutoMonster?style=for-the-badge)](../../releases/latest)

This project aims to automate some tedious tasks in the game Monster Legends, making the gaming experience more
enjoyable and efficient.

## 📚 Table of Contents

- [🎯 Introduction](#-introduction)
- [⚙️ Features](#-features)
- [💻 Installation](#-installation)
- [🔄 Updates](#-updates)
- [🕹️ Setting Up an Emulator](#-setting-up-an-emulator)
- [💬 Usage and Commands](#-usage-and-commands)
- [🚨 Disclaimer](#-disclaimer)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)

## 🎯 Introduction

The Auto Monster Project is a Python-based automation tool for the game Monster Legends. It is designed to handle
repetitive tasks within the game, such as playing ads, doing dungeons, etc. Please note that while the project is
functional, it is still in active development and may undergo changes and improvements.

**Compatibility:** The Auto Monster Project can be used on both phones and tablets, although it is primarily designed
for desktop use.
Mobile compatibility is still under development and may vary depending on the device.

## ⚙️ Features

- Automated playing for Monster-Wood: ✔️ Working
- Era Saga automation: ✔️ Working
- PVP automation: ⚠️ Some issues
- Daily Dungeon automation (Gem and Rune): ✔️ Working
- Cavern Dungeon automation: ✔️ Working
- Maze automation: ❌ Not implemented

## 💻 Installation

To install AutoMonster:

1. Go to the [Releases page](../../releases/latest)
2. Download the **AutoMonster_Setup.exe** installer
3. Run the installer
4. Launch AutoMonster from your Start Menu or desktop shortcut

The installer will:
- Install the program to your local AppData folder
- Create start menu shortcuts
- Optionally create a desktop shortcut
- Handle automatic updates

## 🔄 Updates

AutoMonster includes an automatic update system that will:
- Check for new versions on startup
- Download and install updates automatically
- Maintain your settings and configurations
- Clean up old files after updating

You don't need to download new versions manually - the program will handle everything for you!

## 🕹️ Setting Up an Emulator

To automate tasks in Monster Legends, you'll need to set up an emulator on your computer.

### Step 1: Choose, Download and Install the Emulator an Emulator

There are several emulators available for running Android apps on your computer. Some popular choices include:

- **BlueStacks**: One of the most popular Android emulators, known for its stability and performance.
- **NoxPlayer**: Another reliable emulator with a wide range of features.
- **LDPlayer**: Optimized for gaming, LDPlayer offers smooth gameplay and customization options.

Choose any emulator that has access to adb and can run Android apps on your computer.

### Step 2: Install Monster Legends

After setting up the emulator, it is recommended to install Monster Legends using an APK file and not from the Google
Play Store. APKPure is a good source for APK files since Google Play Store sometimes detects emulators and doesn't allow
you to download the game.

### Step 3: Configure Emulator Settings

To ensure the script run, configure the emulator settings as follows:

- **Resolution**: Set the resolution to 1280x720
- **DPI**: Set the DPI to 240
- **ADB Connection**: Enable ADB connection in the emulator settings to allow communication with the automation scripts.

## 💬 Usage and Commands

While the Auto Monster Project is running, you can use the following commands:

- `era`: Goes through the Era Saga automatically.
- `pvp`: Does PVP battles automatically
- `rd`: Does the daily dungeons automatically (Gem and Rune).
- `ads`: Plays and skips ads in Monster-Wood automatically.
- `cavern`: Does the selected rank-up cavern dungeon automatically.
- `update`: Checks for updates and updates the project if a new version is available. (Not implemented)
- `version`: Displays the current version of the Auto Monster Project.
- `help`: Displays the help menu, listing all available commands and their descriptions. You can also
  use `help [command]` to get more details about a specific command.

You can also chain commands using `&` or `&&`: ❌ Not implemented

- Using `&` between commands will run them concurrently, regardless of the success or failure of the previous command.
- Using `&&` between commands will run the next command only if the previous one succeeded without errors.

### 🚀 Using the Executable

To use the Auto Monster Project with the executable:

1. Download the executable file for the Auto Monster Project from the [release page](../../releases) on GitHub.
2. After downloading, run the executable file to start the automation process.

## 🚨 Disclaimer

The Auto Monster Project is provided for educational and informational purposes only. While efforts have been made to
ensure its reliability and safety, it's essential to understand that the use of automation tools, including this
project, may violate the terms of service of the game Monster Legends.

**Responsibility:** The creator of the Auto Monster Project is not responsible for any consequences that may arise from
the use of this tool. This includes but is not limited to account suspension, banning, or other penalties imposed by the
game developers.

**Usage:** By using the Auto Monster Project, you acknowledge that you are solely responsible for your actions and any
risks associated with using automated tools in online games. It's recommended to review and comply with the terms of
service of Monster Legends and to use the Auto Monster Project responsibly and at your own risk.

## 🤝 Contributing

Contributions to the Auto Monster Project are welcome. If you encounter any bugs or have feature requests, please ask.

## 📜 License

This project is licensed under the MIT License. This allows others to use, modify, and distribute the project, subject
to the terms of the license.

