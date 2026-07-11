import json
import os
import sys

from controller_gui import ControllerGUI
from config.config import CHANGELOG_FILE

from wakepy import keep


def load_update_message(is_updated: bool) -> str:
    """Load the update message for the current version from the changelog.

    Only returns a message when launched with the 'updated' flag,
    so the user sees it after installing a new version.
    """
    if not is_updated:
        return ""

    if not os.path.isfile(CHANGELOG_FILE):
        return ""

    try:
        with open(CHANGELOG_FILE, "r") as f:
            changelog = json.load(f)
    except (json.JSONDecodeError, OSError):
        return ""

    # Read current version
    if not os.path.isfile("version.txt"):
        return ""

    with open("version.txt", "r") as f:
        version = f.read().strip()

    # Look up message for this version
    return changelog.get(version, "")


def main(is_updated: bool = False) -> None:
    try:
        with keep.presenting():
            update_msg = load_update_message(is_updated)
            app = ControllerGUI(update_message=update_msg)
            app.mainloop()
    except Exception as e:
        if e is KeyboardInterrupt:
            return
        if os.path.exists("debug.ban"):
            raise e
        import tkinter.messagebox as msg
        msg.showerror("Error", str(e))


if __name__ == '__main__':
    is_updated = "updated" in sys.argv
    main(is_updated=is_updated)
