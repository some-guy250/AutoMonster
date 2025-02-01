import os
import threading
import time
from tempfile import gettempdir

import customtkinter as ctk
import requests

repo_url_api = "https://api.github.com/repos/some-guy250/AutoMonster"
repo_url = "https://github.com/some-guy250/AutoMonster"


def get_version():
    if os.path.isfile("version.txt"):
        with open("version.txt", "r") as file:
            return file.read().strip()
    return "0.0.0"


__version__ = get_version()  # This is now the main app version


def download_with_progress(url, file_name, progress_bar=None, label=None):
    try:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024

        if progress_bar:
            progress_bar.set(0)
            progress_bar.configure(determinate_speed=1)
            progress_bar.configure(mode="determinate")

        with open(file_name, 'wb') as file:
            downloaded = 0
            for data in response.iter_content(block_size):
                file.write(data)
                downloaded += len(data)
                if progress_bar and total_size:
                    progress = downloaded / total_size
                    progress_bar.set(progress)
                    if label:
                        mb_downloaded = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        label.configure(text=f"Downloading: {mb_downloaded:.1f}MB / {mb_total:.1f}MB")
    except Exception as e:
        raise Exception(f"Download failed: {str(e)}")


def compare_versions(version1, version2):
    v1_parts = version1.split('.')
    v2_parts = version2.split('.')

    # Compare each part of the version.txt number
    for i in range(max(len(v1_parts), len(v2_parts))):
        v1_part = int(v1_parts[i]) if i < len(v1_parts) else 0
        v2_part = int(v2_parts[i]) if i < len(v2_parts) else 0

        if v1_part < v2_part:
            return -1
        elif v1_part > v2_part:
            return 1

    # All parts are equal, versions are the same
    return 0


def check_for_updates():
    try:
        response = requests.get(f"{repo_url_api}/releases/latest")
        latest_release = response.json()
        latest_version = latest_release['tag_name'].replace("v-", "")
        return compare_versions(latest_version, __version__) == 1, latest_version
    except Exception as e:
        print(f"Failed to check for updates: {str(e)}")
        return False, None


def download_assets():
    # Send a GET request to the GitHub API to retrieve information about the contents of the "assets" folder
    response = requests.get(f"{repo_url_api}/contents/assets")

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        contents = response.json()

        # Create the "assets" folder if it doesn't exist
        assets_folder = "assets"
        if not os.path.exists(assets_folder):
            os.makedirs(assets_folder)

        total_files = len(contents)
        for i, item in enumerate(contents):
            # Check if the item is a file
            if item["type"] == "file":
                # Get the download URL for the file
                download_url = item["download_url"]

                # Extract the file name from the URL
                file_name = os.path.basename(download_url)

                # Define the file path to save the file
                file_path = os.path.join(assets_folder, file_name)

                # Send a GET request to download the file
                response = requests.get(download_url)

                # Save the file
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                # Update progress in GUI
                progress = (i + 1) / total_files
                if hasattr(ctk, '_running_app') and ctk._running_app:
                    app = ctk._running_app
                    app.update_progress(progress, f"Downloading assets: {i+1}/{total_files}")
    else:
        print(f"Failed to retrieve contents. Status code: {response.status_code}")


def launch_main(updated=False):
    # run AutoMonster.exe and add updated flag to the command
    # if updated is True delete the assets folder (if it exists) to remove old files that are no longer needed
    if updated:
        if os.path.exists("assets"):
            for file in os.listdir("assets"):
                os.remove(f"assets/{file}")
            os.rmdir("assets")
        download_assets()
    os.system(f"start AutoMonster.exe {'updated' if updated else ''}")


def save_version(version):
    with open("version.txt", "w") as file:
        file.write(version)


class UpdaterGUI(ctk.CTk):
    def __init__(self, latest_version, force_update=False):
        super().__init__()
        self.latest_version = latest_version
        self.download_thread = None
        self.cancel_download = False

        # Window setup
        self.title("AutoMonster Updater")
        self.geometry("400x250")
        self.resizable(False, False)
        self.center_window()

        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Update the status labels
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Welcome to AutoMonster!" if force_update else f"Version {latest_version} is available!",
            font=("Roboto", 14, "bold")
        )
        self.title_label.pack(pady=(20, 5))

        update_label = ctk.CTkLabel(
            self.main_frame,
            text="Downloading required files..." if force_update else "A new update is available.",
            font=("Roboto", 12)
        )
        update_label.pack(pady=(0, 20))

        # Progress bar (hidden initially)
        self.progress = ctk.CTkProgressBar(self.main_frame, width=300)
        self.progress.pack(pady=20)
        self.progress.set(0)
        self.progress.configure(mode="determinate")  # Set mode here instead of during download

        # Status label (hidden initially)
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=("Roboto", 14)
        )
        self.status_label.pack(pady=20)

        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame)
        btn_frame.pack(fill="x", pady=10)

        if force_update:
            # For initial install, start download automatically
            self.after(100, self.download_update)
        else:
            # hide the progress bar and status label
            self.progress.pack_forget()
            self.status_label.pack_forget()

            # Show update options for normal updates
            update_btn = ctk.CTkButton(
                btn_frame,
                text="Update Now",
                command=self.download_update
            )
            update_btn.pack(side="left", padx=10, expand=True)

            skip_btn = ctk.CTkButton(
                btn_frame,
                text="Skip Update",
                command=self.skip_update,
                fg_color="transparent",
                border_width=2
            )
            skip_btn.pack(side="right", padx=10, expand=True)

        # Add this line after initializing the window
        ctk._running_app = self

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def show_error(self, message):
        error_window = ctk.CTkToplevel(self)
        error_window.title("Error")
        error_window.geometry("300x150")

        error_label = ctk.CTkLabel(
            error_window,
            text=message,
            wraplength=250
        )
        error_label.pack(pady=20)

        ok_btn = ctk.CTkButton(
            error_window,
            text="OK",
            command=error_window.destroy
        )
        ok_btn.pack(pady=10)

    def skip_update(self):
        self.destroy()
        launch_main(False)

    def update_progress(self, progress, status_text=None):
        try:
            self.progress.set(progress)
            if status_text:
                self.status_label.configure(text=status_text)
            self.update_idletasks()  # Force GUI update
        except Exception:
            pass  # Ignore errors if window is closed

    def download_and_install(self):
        try:
            self.status_label.configure(text="Preparing download...")
            response = requests.get(f"{repo_url_api}/releases/latest")
            latest_release = response.json()
            assets = latest_release['assets']

            # Only look for main executable
            main_exe = next((asset for asset in assets if asset['name'] == 'AutoMonster.exe'), None)

            if not main_exe:
                raise Exception("AutoMonster.exe not found in release")

            temp_dir = gettempdir()
            temp_file = f"{temp_dir}/AutoMonster.exe"

            # Download and install main exe
            self.download_file(main_exe['browser_download_url'], temp_file)

            # Install update
            self.after(0, lambda: self.status_label.configure(text="Installing update..."))

            # Copy file to current directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            os.replace(temp_file, f"{current_dir}/AutoMonster.exe")

            # Download assets after installing main executable
            self.after(0, lambda: self.status_label.configure(text="Downloading assets..."))
            download_assets()

            # Save version and complete
            save_version(self.latest_version)
            self.after(0, self.complete_update)

        except Exception as e:
            self.after(0, lambda: self.handle_error(str(e)))

    def download_file(self, url, filepath):
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        start_time = time.time()
        last_downloaded = 0
        last_time = start_time

        status_format = "Downloading update: {:.1f}MB / {:.1f}MB (ETA: {})"

        with open(filepath, 'wb') as file:
            for data in response.iter_content(block_size):
                if self.cancel_download:
                    file.close()
                    os.remove(filepath)
                    self.after(0, self.handle_cancel)
                    return

                file.write(data)
                downloaded += len(data)
                current_time = time.time()

                if current_time - last_time >= 1:
                    self.update_download_progress(downloaded, total_size, last_downloaded,
                                                  current_time, last_time, status_format)
                    last_downloaded = downloaded
                    last_time = current_time

    def handle_cancel(self):
        self.destroy()
        launch_main(False)

    def handle_error(self, error_msg):
        self.show_error(f"Failed to download update: {error_msg}")
        if __version__ == "0.0.0":
            self.destroy()
        else:
            self.skip_update()

    def complete_update(self):
        self.destroy()
        launch_main(True)

    def download_update(self):
        # Show progress bar and status label
        self.progress.pack(pady=20)
        self.status_label.pack(pady=20)
        self.status_label.configure(text="Starting download...")
        self.progress.set(0)  # Reset progress

        # Replace update button with cancel button
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                widget.destroy()

        cancel_btn = ctk.CTkButton(
            self.main_frame,
            text="Cancel",
            command=self.cancel_download_thread,
            fg_color="transparent",
            border_width=2
        )
        cancel_btn.pack(pady=10)

        # Start download thread
        self.download_thread = threading.Thread(target=self.download_and_install)
        self.download_thread.daemon = True
        self.download_thread.start()

    def cancel_download_thread(self):
        self.cancel_download = True
        self.status_label.configure(text="Cancelling...")


def main():
    update_available, latest_version = check_for_updates()

    ctk.set_default_color_theme("dark-blue")

    if __version__ == "0.0.0" or update_available:
        app = UpdaterGUI(latest_version, force_update=(__version__ == "0.0.0"))
        app.mainloop()
    else:
        launch_main(False)


if __name__ == "__main__":
    main()
