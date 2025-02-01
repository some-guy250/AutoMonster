import sys
from gui import ControllerGUI
from tkinter import messagebox
import os
import requests
import tempfile
import time

def main():
    try:
        # Check if app was launched after update
        updated = len(sys.argv) > 1 and sys.argv[1] == "updated"

        app = ControllerGUI()
        if app.all_good:
            app.mainloop()
    except Exception as e:
        if e is KeyboardInterrupt:
            return
        if os.path.exists("debug.ban"):
            raise e
        messagebox.showerror("Error", str(e))

if __name__ == '__main__':
    main()
