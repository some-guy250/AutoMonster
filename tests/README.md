# AutoMonster Tests

Standalone test scripts for AutoMonster. These are **not** bundled with the build — they run independently from the project root.

## Running Tests

Activate the venv first, then run from the project root:

```powershell
.\venv\Scripts\Activate.ps1
python tests\dungeon_checker.py
```

## Available Tests

### `dungeon_checker.py`
Navigates to the caverns screen and checks which cavern assets are visible on screen. Reports a summary of found vs. missing caverns.

- **Exit 0**: All cavern assets detected
- **Exit 1**: Some caverns not detected (templates may need updating after game patch)
- **Exit 2**: Script error (device connection, navigation failure, etc.)
