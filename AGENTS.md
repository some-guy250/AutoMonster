# AutoMonster - Agent Context

## What It Is
Python automation tool for Monster Legends using ADB/scrcpy + OpenCV template matching.

## Folder Structure
```
AutoMonster/
├── main.py, launcher.py          # Entry points
├── AutoMonster.py                # Main Controller class
├── controller_gui.py             # GUI orchestrator
├── device_manager.py             # ADB/device control
├── navigator.py                  # Game navigation
├── utils/                        # Utilities
│   ├── AutoMonsterErrors.py      # Exception classes (import with *)
│   ├── HelperFunctions.py        # Image comparison
│   ├── assets.py                 # Asset loading (ASSETS enum)
│   ├── config_manager.py         # JSON config with validation
│   ├── logger.py                 # Logging setup
│   ├── update_utils.py           # Version/ETA helpers
│   └── vision_manager.py         # OpenCV template matching
├── config/                       # Configuration
│   ├── config.py                 # Thresholds, timeouts, coordinates
│   └── regions.py                # Template matching regions
├── gui/                          # GUI components
│   ├── command_frame.py          # Command UI
│   ├── debug_tool.py             # Debug visualization
│   ├── debug_widgets.py          # Debug widgets
│   ├── debug_unlock.py           # Unlock automation
│   ├── device_selection_frame.py # Device picker
│   ├── gui_config.py             # GUI constants
│   ├── gui_events.py             # Event handlers
│   ├── gui_frames.py             # UI builders
│   └── macro_dialog.py           # Macro UI
├── features/                     # Game features
│   ├── ads.py, battle.py, game.py, monster.py
└── asset_images/                 # PNG templates
```

## Import Patterns
```python
# Assets
from utils.assets import ASSETS

# Config values
from config.config import GAME_HEIGHT, DEFAULT_TEMPLATE_THRESHOLD

# Regions
from config.regions import ASSET_REGIONS, Region

# Errors (wildcard import)
from utils.AutoMonsterErrors import *

# GUI (relative imports inside gui/)
from .debug_tool import DebugTool
```

## Key Patterns
- `progress_callback(float)` for long operations (0.0 to 1.0)
- `screenshot` parameter avoids redundant captures

## Implementation Style
When implementing something new, check how similar things were done before and follow the same style:
- Look at existing features in `features/` for patterns
- Check `AutoMonster.py` for method signatures and parameter patterns
- Follow existing error handling, logging, and callback patterns
- Don't invent new patterns if one already exists

## Error Handling
Custom exceptions in `utils/AutoMonsterErrors.py`:
- `AutoMonsterError` (base)
- `ExecutionFlag` (flow control, not error)
- Feature-specific: `BattleError`, `GoToError`, `ClickError`, etc.

Catch with: `except AutoMonsterError as e:`

## Building
Handled by GitHub Actions (`.github/workflows/build_and_release.yml`):
- Triggers on `version.txt` changes
- Builds EXE with PyInstaller
- Creates installer with Inno Setup
- Publishes to GitHub releases


## Virtual Environment
- **ALWAYS use the venv** for running, installing packages, and testing
- Activate with: `./venv/Scripts/Activate.ps1` (PowerShell) or `venv\Scripts\activate` (CMD)
- Run with: `python main.py` (after activating) or `./venv/Scripts/python.exe main.py`
- Install packages with: `./venv/Scripts/python.exe -m pip install <package>`
- **NEVER install packages in the global Python**, use the venv only

## Important Notes
- All thresholds/coordinates in `config/config.py`
- Folder structure: `utils/`, `config/`, `gui/` packages
- No version fallbacks: expect latest version
- **No `print()` statements**: Use `logger.info/debug/error()` or `controller.log_gui()` for user-facing output
- Update AGENTS.md when structure/patterns change
- Temp files: use `_filename.py` prefix for dev scripts, delete after use

## Adding New Assets
When user pastes asset capture output like:
```
  - ASSETNAME = "assetname.png" (region: x,y,wxh)
```
1. Add to `utils/assets.py`:
   ```python
   AssetName = "assetname.png"
   ```
2. Add to `config/regions.py` **Never assume a region** only set regions when explicitly told what they are:
   ```python
   ASSETS.AssetName: Region.ALL,
   ```

## Changelog
- `changelog.json` contains version entries with `subtitle` and `changes` (list of bullet points)
- Format: `{ "3.0.0": { "subtitle": "...", "changes": ["...", "..."] } }`
- The "What's New" dialog displays subtitle as sub-header and changes as bullet points
- **ONLY the user** writes/edits changelog content — the agent never modifies the message text

## GitHub / Release Workflow
**IMPORTANT: Only push or trigger releases when explicitly told by the user.**

**GitHub Account:**
- This project uses `some-guy250` account
- Local git config: `user.name = some-guy250`, `user.email = some-guy250@users.noreply.github.com`
- gh CLI: `some-guy250` is the active account for this repo

**Push Commands:**
```powershell
git push                    # Push to remote
gh workflow run build_and_release.yml  # Trigger release build
```

**Release Workflow** (when user says "make a new release" or "push for release"):
1. Ask/confirm main app version number (e.g., "3.0.0")
2. Ask if launcher code changed (if yes, ask for launcher version)
3. **CHECK: Has changelog content been written?**
   - If `changelog.json` has no entry for the version, DO NOT proceed — tell the user to write the changelog first
   - Only continue once the user confirms the changelog is ready
4. Update `version.txt` (always)
5. Update `launcher_version.txt` (only if launcher code changed)
6. Update `changelog.json` with new version entry (user provides content)
7. Commit: "Release v{version}"
8. Push (triggers GitHub Actions automatically)
9. GitHub Actions builds EXE + installer, publishes release

**Build Issues:**
- Inno Setup download may corrupt — fix is to use `Invoke-WebRequest` instead of `curl` in workflow
