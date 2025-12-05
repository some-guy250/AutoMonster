import os
import threading
import time
import tkinter as tk
import sys
import subprocess
from tempfile import gettempdir
from tkinter import ttk

import requests

repo_url_api = "https://api.github.com/repos/some-guy250/AutoMonster"
repo_url = "https://github.com/some-guy250/AutoMonster"


class ModernProgressWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AutoMonster Updater")
        self.root.geometry("400x250")
        self.root.resizable(False, False)
        self.root.configure(bg='#2b2b2b')

        # Set window icon
        if os.path.exists("assets/favicon.ico"):
            self.root.iconbitmap("assets/favicon.ico")

        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 250) // 2
        self.root.geometry(f"400x250+{x}+{y}")

        # Update style configuration
        self.style = ttk.Style(self.root)
        self.style.theme_use('default')  # Use default theme as base
        self.style.layout('Custom.Horizontal.TProgressbar',
                          [('Horizontal.Progressbar.trough',
                            {'children': [('Horizontal.Progressbar.pbar',
                                           {'side': 'left', 'sticky': 'ns'})],
                             'sticky': 'nswe'})])
        self.style.configure('Custom.Horizontal.TProgressbar',
                             thickness=15,
                             troughcolor='#404040',
                             background='#00ff00',
                             borderwidth=0)

        # Title Frame
        title_frame = tk.Frame(self.root, bg='#2b2b2b')
        title_frame.pack(pady=20)

        tk.Label(title_frame,
                 text="AutoMonster Updater",
                 font=("Helvetica", 16, "bold"),
                 fg='#ffffff',
                 bg='#2b2b2b').pack()

        # Main Frame
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill='both', expand=True, padx=20)

        # Status Label
        self.label = tk.Label(main_frame,
                              text="Checking for updates...",
                              font=("Helvetica", 10),
                              fg='#ffffff',
                              bg='#2b2b2b')
        self.label.pack(pady=(0, 10))

        # Progress Frame
        progress_frame = tk.Frame(main_frame, bg='#2b2b2b')
        progress_frame.pack(fill='x', pady=10)

        # Update progress bar creation
        self.progress = ttk.Progressbar(progress_frame,
                                        style="Custom.Horizontal.TProgressbar",
                                        length=360,
                                        mode='determinate')
        self.progress.pack()

        # Details Label
        self.details = tk.Label(main_frame,
                                text="",
                                font=("Helvetica", 9),
                                fg='#aaaaaa',
                                bg='#2b2b2b',
                                wraplength=360)
        self.details.pack(pady=10)

        # Add global ETA label after details
        self.global_eta = tk.Label(main_frame,
                                   text="",
                                   font=("Helvetica", 9),
                                   fg='#aaaaaa',
                                   bg='#2b2b2b')
        self.global_eta.pack(pady=5)

        # Version Frame
        version_frame = tk.Frame(self.root, bg='#2b2b2b')
        version_frame.pack(side='bottom', pady=15)

        self.version_label = tk.Label(version_frame,
                                      text="Current Version: checking...",
                                      font=("Helvetica", 8),
                                      fg='#888888',
                                      bg='#2b2b2b')
        self.version_label.pack()

        # Add smooth animation for progress updates
        self.target_progress = 0
        self.current_progress = 0
        
        # State for polling
        self.pending_progress = 0
        self.pending_text = ""
        self.pending_details = ""
        self.pending_eta = ""
        self.needs_update = False
        
        self.animate_progress()
        self.poll_updates()

        self.is_closing = False
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.is_closing = True
        self.root.quit()
        self.root.destroy()

    def safe_update(self, func):
        """Thread-safe update method"""
        if not self.is_closing:
            self.root.after(0, func)

    def poll_updates(self):
        """Periodically update UI from shared state"""
        if self.needs_update:
            self.target_progress = self.pending_progress
            if self.pending_text:
                self.label['text'] = self.pending_text
            if self.pending_details:
                self.details['text'] = self.pending_details
            if self.pending_eta:
                self.global_eta['text'] = self.pending_eta
            self.needs_update = False
        
        if not self.is_closing:
            self.root.after(50, self.poll_updates)  # Check every 50ms

    def animate_progress(self):
        if self.current_progress < self.target_progress:
            self.current_progress += 0.5  # Faster animation
            if self.current_progress > self.target_progress:
                self.current_progress = self.target_progress
            self.progress['value'] = self.current_progress
        elif self.current_progress > self.target_progress:
            self.current_progress = self.target_progress
            self.progress['value'] = self.current_progress

        if not self.is_closing:
            self.root.after(10, self.animate_progress)

    def update_progress(self, value, text="", details=""):
        self.pending_progress = value
        if text:
            self.pending_text = text
        if details:
            self.pending_details = details
        self.needs_update = True

    def update_version(self, current_ver, latest_ver=None):
        def update():
            if latest_ver:
                self.version_label['text'] = f"Current: v{current_ver} → Latest: v{latest_ver}"
            else:
                self.version_label['text'] = f"Current Version: v{current_ver}"
        self.safe_update(update)

    def update_eta(self, eta_text):
        self.pending_eta = eta_text
        self.needs_update = True

    def close(self):
        def do_close():
            if not self.is_closing:
                self.is_closing = True
                self.root.quit()
                self.root.destroy()

        self.safe_update(do_close)


def get_version():
    if os.path.isfile("version.txt"):
        with open("version.txt", "r") as file:
            return file.read().strip()
    return "0.0.0"


def compare_versions(version1, version2):
    v1_parts = version1.split('.')
    v2_parts = version2.split('.')
    for i in range(max(len(v1_parts), len(v2_parts))):
        v1_part = int(v1_parts[i]) if i < len(v1_parts) else 0
        v2_part = int(v2_parts[i]) if i < len(v2_parts) else 0
        if v1_part < v2_part:
            return -1
        elif v1_part > v2_part:
            return 1
    return 0


def check_for_updates():
    try:
        response = requests.get(f"{repo_url_api}/releases/latest")
        latest_release = response.json()
        latest_version = latest_release['tag_name'].replace("v-", "")
        current_version = get_version()
        return (compare_versions(latest_version, current_version) == 1, latest_version)
    except:
        return (False, None)


def format_time(seconds):
    """Convert seconds to human readable time"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        seconds = int(seconds % 60)
        return f"{minutes}m {seconds}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"


def calculate_eta(start_time, current_progress, total_size):
    """Calculate estimated time remaining"""
    if current_progress == 0:
        return "Calculating..."

    elapsed = time.time() - start_time
    rate = current_progress / elapsed  # bytes per second
    remaining_bytes = total_size - current_progress

    if rate > 0:
        eta_seconds = remaining_bytes / rate
        return format_time(eta_seconds)
    return "Calculating..."


def format_size(size):
    """Convert bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def download_assets(progress_window=None):
    if progress_window:
        progress_window.update_progress(0, "Preparing to download assets...", "Fetching file information...")

    if os.path.exists("assets"):
        for fname in os.listdir("assets"):
            os.remove(f"assets/{fname}")
        os.rmdir("assets")
    os.makedirs("assets", exist_ok=True)

    response = requests.get(f"{repo_url_api}/contents/assets")
    if response.status_code == 200:
        contents = response.json()
        files_to_download = [item for item in contents if item["type"] == "file"]
        total_files = len(files_to_download)

        # Calculate total size
        if progress_window:
            progress_window.update_progress(0, "Preparing download...", "Calculating total size...")

        total_size = sum(item["size"] for item in files_to_download)

        start_time = time.time()
        total_downloaded = 0

        for idx, item in enumerate(files_to_download):
            file_name = os.path.basename(item["download_url"])
            file_path = os.path.join("assets", file_name)
            response = requests.get(item["download_url"], stream=True)

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):
                    f.write(chunk)
                    total_downloaded += len(chunk)
                    
                    if progress_window and total_size:
                        current_progress = (total_downloaded / total_size) * 50
                        eta = calculate_eta(start_time, total_downloaded, total_size)
                        speed = total_downloaded / (time.time() - start_time)

                        # Update main progress with current file info
                        status = (
                            f"File {idx + 1}/{total_files}: {file_name}\n"
                            f"Total Progress: {format_size(total_downloaded)} / {format_size(total_size)}"
                        )

                        # Update global ETA separately
                        global_status = (
                            f"Speed: {format_size(speed)}/s | ETA: {eta}"
                        )

                        progress_window.update_progress(
                            current_progress,
                            "Downloading assets...",
                            status
                        )
                        progress_window.update_eta(global_status)


def download_file(url, target_path, progress_window=None, progress_start=0, progress_end=100, label="Downloading..."):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    start_time = time.time()
    downloaded = 0
    
    with open(target_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=65536):
            file.write(chunk)
            downloaded += len(chunk)
            
            if progress_window and total_size:
                current_percent = (downloaded / total_size)
                
                progress = progress_start + (current_percent * (progress_end - progress_start))
                eta = calculate_eta(start_time, downloaded, total_size)
                speed = downloaded / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
                
                status = (
                    f"{label}\n"
                    f"{format_size(downloaded)} / {format_size(total_size)} ({int(current_percent * 100)}%)"
                )
                
                global_status = f"Speed: {format_size(speed)}/s | ETA: {eta}"
                
                progress_window.update_progress(progress, label, status)
                progress_window.update_eta(global_status)

def get_launcher_version():
    if os.path.isfile("launcher_version.txt"):
        with open("launcher_version.txt", "r") as file:
            return file.read().strip()
    return "0.0.0"

def self_update(latest_release, progress_window):
    assets = latest_release.get('assets', [])
    
    # Check for version file in assets
    version_asset = next((a for a in assets if a['name'] == 'launcher_version.txt'), None)
    launcher_asset = next((a for a in assets if a['name'] in ['LauncherAutoMonster.exe', 'Launcher.bin']), None)
    
    if not launcher_asset:
        return False

    should_update = False
    new_version = None

    if version_asset:
        try:
            response = requests.get(version_asset['browser_download_url'])
            if response.status_code == 200:
                new_version = response.text.strip()
                local_version = get_launcher_version()
                if compare_versions(new_version, local_version) == 1:
                    should_update = True
        except Exception as e:
            print(f"Error checking launcher version: {e}")
    
    # Fallback to size check if version check failed or file missing
    current_exe = sys.executable
    if not should_update and getattr(sys, 'frozen', False) and not new_version:
        local_size = os.path.getsize(current_exe)
        remote_size = launcher_asset['size']
        if local_size != remote_size:
            should_update = True

    if should_update and getattr(sys, 'frozen', False):
        progress_window.update_progress(0, "Updating Launcher...", "Downloading new version...")
        
        new_launcher_path = current_exe + ".new"
        download_file(launcher_asset['browser_download_url'], new_launcher_path, progress_window, 0, 100, "Downloading Launcher update...")
        
        # Update the version file locally
        if new_version:
            with open("launcher_version.txt", "w") as f:
                f.write(new_version)

        # Rename dance
        old_launcher_path = current_exe + ".old"
        if os.path.exists(old_launcher_path):
            os.remove(old_launcher_path)
            
        os.rename(current_exe, old_launcher_path)
        os.rename(new_launcher_path, current_exe)
        
        # Restart
        subprocess.Popen([current_exe])
        sys.exit(0)
        return True
    return False

def download_main_exe(progress_window=None):
    if progress_window:
        progress_window.update_progress(50, "Downloading main executable...")
        progress_window.update_eta("")  # Clear previous ETA

    response = requests.get(f"{repo_url_api}/releases/latest")
    latest_release = response.json()
    assets = latest_release['assets']
    # Look for AutoMonster.exe or AutoMonster.bin
    main_exe = next((asset for asset in assets if asset['name'] in ['AutoMonster.exe', 'AutoMonster.bin']), None)
    if not main_exe:
        raise Exception("AutoMonster.exe not found in release")

    temp_dir = gettempdir()
    temp_file = os.path.join(temp_dir, "AutoMonster_new.exe")
    
    download_file(main_exe['browser_download_url'], temp_file, progress_window, 50, 100, "Downloading main executable...")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        # Ensure we use correct paths
        batch_path = "replace.bat"  # Use relative path since it's in the same directory
        target_path = "AutoMonster.exe"  # Use relative path
        
        # Use subprocess with simplified paths
        import subprocess
        process = subprocess.run([batch_path, temp_file, target_path], 
                               shell=True,
                               capture_output=True,
                               text=True)
        
        if process.returncode != 0:
            raise Exception(f"Failed to replace executable file: {process.stderr}")
            
    except Exception as e:
        import tkinter.messagebox as msg
        msg.showerror("Error", f"Error replacing main executable: {e}")
        raise e


def launch_main(updated=False):
    os.system(f"start AutoMonster.exe {'updated' if updated else ''}")


def save_version(version):
    with open("version.txt", "w") as file:
        file.write(version)


def update_process(progress_window, latest_version):
    try:
        # Check for self-update first
        response = requests.get(f"{repo_url_api}/releases/latest")
        latest_release = response.json()
        
        if self_update(latest_release, progress_window):
            return # self_update will restart the process

        progress_window.update_progress(0, "Initializing update...", "Starting download process...")
        download_assets(progress_window)
        download_main_exe(progress_window)
        if latest_version:
            save_version(latest_version)
        progress_window.update_progress(100, "Update completed!", "Starting AutoMonster...")
        time.sleep(1)
        # Set up the launch before closing
        launch_main(True)
        # Signal the main thread to close the window
        progress_window.close()
    except Exception as e:
        if not progress_window.is_closing:
            progress_window.update_progress(0, "Error during update!", str(e))
            time.sleep(3)
            progress_window.close()


def main():
    update_needed, latest_version = check_for_updates()
    local_version = get_version()

    if local_version == "0.0.0" or update_needed:
        progress_window = ModernProgressWindow()
        progress_window.update_version(local_version, latest_version)
        update_thread = threading.Thread(target=update_process, args=(progress_window, latest_version))
        update_thread.daemon = True  # Make thread daemon
        update_thread.start()
        progress_window.root.mainloop()
    else:
        launch_main(False)


if __name__ == "__main__":
    main()
