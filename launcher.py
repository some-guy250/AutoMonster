import os
import subprocess

def launch_main():
    """Launches the main AutoMonster executable locally."""
    exe_name = "AutoMonster.exe"
    
    if os.path.exists(exe_name):
        # Use Popen to launch without blocking
        subprocess.Popen([exe_name])
    else:
        import tkinter as tk
        import tkinter.messagebox as msg
        root = tk.Tk()
        root.withdraw()
        msg.showerror("Error", f"{exe_name} not found in the current directory.\nPlease install the application manually.")
        root.destroy()

def main():
    launch_main()

if __name__ == "__main__":
    main()