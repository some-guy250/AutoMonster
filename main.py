import os
import sys
import importlib
import subprocess
from tkinter import messagebox


def check_dependencies():
    packages = {
        "pkg_resources": "setuptools",
        "scrcpy": "scrcpy-client",
        "adbutils": "adbutils",
        "wakepy": "wakepy",
        "customtkinter": "customtkinter"
    }

    missing = []

    for module, package in packages.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(package)

    if missing:
        try:
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                *missing
            ])

        except Exception as e:
            messagebox.showerror(
                "Dependency Error",
                f"Could not install missing packages:\n\n{e}"
            )
            sys.exit(1)


# Run before importing your own files
check_dependencies()


from controller_gui import ControllerGUI
from wakepy import keep


def main():
    try:
        # Check if app was launched after update
        updated = len(sys.argv) > 1 and sys.argv[1] == "updated"

        with keep.presenting():
            app = ControllerGUI()
            app.mainloop()

    except KeyboardInterrupt:
        return

    except Exception as e:
        if os.path.exists("debug.ban"):
            raise e

        messagebox.showerror(
            "Error",
            str(e)
        )


if __name__ == '__main__':
    main()