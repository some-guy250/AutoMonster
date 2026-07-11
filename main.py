import os
import sys

from controller_gui import ControllerGUI
from gui.gui_frames import _get_changelog_entry

from wakepy import keep


def load_update_message(is_updated: bool) -> dict:
    """Load the changelog entry for the current version.

    Only returns an entry when launched with the 'updated' flag,
    so the user sees it after installing a new version.
    Returns a dict with 'subtitle' and 'changes' keys.
    """
    if not is_updated:
        return {}

    return _get_changelog_entry()


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
