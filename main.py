import sys
from gui import ControllerGUI
from tkinter import messagebox
import os
import requests
import tempfile
import time
import threading

def update_launcher():
    try:
        # Get latest release info
        response = requests.get("https://api.github.com/repos/some-guy250/AutoMonster/releases/latest")
        latest_release = response.json()
        launcher_asset = next((asset for asset in latest_release['assets'] 
                             if asset['name'] == 'LauncherAutoMonster.exe'), None)
        
        if launcher_asset:
            # Download new launcher to temp file
            temp_path = os.path.join(tempfile.gettempdir(), "LauncherAutoMonster.exe")
            response = requests.get(launcher_asset['browser_download_url'])
            
            with open(temp_path, "wb") as f:
                f.write(response.content)
                
            # Replace old launcher
            current_dir = os.path.dirname(os.path.abspath(__file__))
            launcher_path = os.path.join(current_dir, "LauncherAutoMonster.exe")
            
            # Wait for launcher process to end
            time.sleep(1)
            
            # Replace file
            os.replace(temp_path, launcher_path)
            return True
    except:
        return False
    return False

def main():
    try:
        # Check if app was launched after update
        updated = len(sys.argv) > 1 and sys.argv[1] == "updated"
        
        # If launched after update, start update process in background
        if updated:
            update_thread = threading.Thread(target=update_launcher, daemon=True)
            update_thread.start()

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
