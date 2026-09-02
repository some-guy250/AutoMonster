"""Main GUI orchestrator for AutoMonster.

Delegates UI construction to gui_frames.py and event handling to gui_events.py.
"""

import logging
import os
import sys
import threading
from datetime import datetime
from typing import Callable, Optional
import pathlib
import subprocess

import numpy as np

import customtkinter as ctk
import amscrcpy

from utils.AutoMonsterErrors import AutoMonsterError, ExecutionFlag
from AutoMonster import Controller
from gui import theme
from gui.command_registry import COMMANDS, PROGRESS_COMMANDS, get_spec
from gui.command_frame import CommandFrame, collect_param_values
from gui.device_selection_frame import DeviceSelectionFrame
from gui.macro_dialog import MacroDialog
from utils.config_manager import ConfigManager
from gui.gui_frames import build_main_interface, _show_update_message_dialog
from gui.gui_events import (
    on_scrcpy_frame, blit_pending_frame,
    on_mouse_down, on_mouse_move, on_mouse_up, on_preview_scroll,
    on_window_resize, on_log_scroll, on_auto_scroll_toggle,
)

if os.path.isfile("version.txt"):
    with open("version.txt", "r") as file:
        __version__ = file.read().strip()


class ControllerGUI(ctk.CTk):
    def __init__(self, update_message: dict = {}) -> None:
        super().__init__()

        self.update_message = update_message

        if os.path.exists("assets/favicon.ico"):
            self.iconbitmap("assets/favicon.ico")

        self.title("AutoMonster")
        self.minsize(400, 450)
        # Resizable so a long connection error (which wraps, see the status
        # label) can be read by growing the window instead of clipping.
        self.resizable(True, True)

        self.config_manager = ConfigManager()
        self.macros = self.config_manager.get_macros()
        self.macro_options = self.config_manager.get_macro_options()
        self.command_specs = COMMANDS

        self.macro_running = False
        self.stop_macro = False
        self.command_running = False
        self._zoom_busy = False

        self.device_frame = DeviceSelectionFrame(self, self.on_device_selected)
        self.main_frame = ctk.CTkFrame(self)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.show_device_selection()

    # =====================================================================
    # Device selection
    # =====================================================================

    def show_device_selection(self) -> None:
        self.main_frame.pack_forget()
        self.device_frame.pack(expand=True, fill="both", padx=20, pady=20)
        self.center_window()
        # Wrap long connection errors to the window width so they stay on the
        # fixed-size screen instead of running off the right edge.
        self.device_frame.set_status_wraplength(self.winfo_width() - 50)

    def show_main_interface(self) -> None:
        self.device_frame.pack_forget()
        self.main_frame.pack(expand=True, fill="both")
        self.geometry("1200x800")
        self.state("zoomed")
        self.resizable(True, True)

        # Show update message dialog after a short delay (only if launched after an update)
        if self.update_message:
            self.after(2000, lambda: _show_update_message_dialog(self.update_message))

    def center_window(self) -> None:
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def on_device_selected(self, device_serial: str) -> None:
        self.device_frame.disable_connect_btns()
        self.device_frame.show_loading("Connecting to device...")
        self._connection_error = None

        def initialize_controller():
            self.controller = None
            self._connection_error = None
            try:
                self.controller = Controller(serial=device_serial)
            except Exception as e:
                self._connection_error = str(e)
                logging.error(f"Failed to connect to device: {e}")

        thread = threading.Thread(target=initialize_controller, daemon=True)
        thread.start()
        self._check_connection_thread(thread)

    def _check_connection_thread(self, thread: threading.Thread) -> None:
        if thread.is_alive():
            self.after(100, lambda: self._check_connection_thread(thread))
            return

        self.device_frame.hide_loading()

        if self.controller is None:
            self.device_frame.enable_connect_btns()
            error_msg = self._connection_error or "Unknown error"
            self.device_frame.status.configure(
                text=f"Connection failed: {error_msg}\nSelect a device and try again",
                text_color="red"
            )
            return

        self.init_main_interface()
        self.show_main_interface()

    # =====================================================================
    # Main interface init
    # =====================================================================

    def init_main_interface(self) -> None:
        self.debug_mode = False

        build_main_interface(self)

        if len(sys.argv) > 1:
            self.append_log(f"Updated to the latest version: v-{__version__}")
        else:
            self.append_log(f"AutoMonster v-{__version__} started")

        if os.path.exists("debug.ban"):
            self.toggle_debug_mode()

    def override_parameter_defaults(self) -> None:
        loaded_defaults = self.config_manager.defaults
        logging.debug("Loaded defaults")
        for cmd_name, spec in self.command_specs.items():
            saved = loaded_defaults.get(cmd_name, {})
            for param_name, config in spec.params.items():
                if param_name in saved:
                    config["default"] = saved[param_name]

    # =====================================================================
    # Logging
    # =====================================================================

    def append_log(self, message: str, level: str = "info") -> None:
        """Append a log entry, safe to call from any thread.

        tkinter is not thread-safe, so the widget update is scheduled on
        the Tk main thread. Calling insert/see from a worker thread can
        intermittently freeze the main loop.
        """
        if level == "debug" and not self.debug_mode:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        try:
            self.after(0, self._append_log_now, log_entry, level)
        except Exception:
            # Tk interpreter is shutting down: dropping the line is fine.
            pass

    def _append_log_now(self, log_entry: str, level: str) -> None:
        """Main thread part of append_log."""
        self.log_text.insert("end", log_entry, level)
        if self.auto_scroll.get():
            self.log_text.see("end")

    # =====================================================================
    # Event handler wrappers (delegate to gui_events module)
    # =====================================================================

    def on_scrcpy_frame(self, frame: np.ndarray) -> None:
        """Scrcpy stream thread entry point: render the newest frame off the main thread (see gui_events)."""
        on_scrcpy_frame(self, frame)

    def blit_pending_frame(self) -> None:
        """Main thread entry point: display the newest rendered image (see gui_events)."""
        blit_pending_frame(self)

    def on_mouse_down(self, event: object) -> None:
        on_mouse_down(self, event)

    def on_mouse_move(self, event: object) -> None:
        on_mouse_move(self, event)

    def on_mouse_up(self, event: object) -> None:
        on_mouse_up(self, event)

    def on_preview_scroll(self, event: object) -> None:
        on_preview_scroll(self, event)

    def queue_zoom(self, direction: str) -> None:
        """Run one pinch zoom off the main thread.

        zoom_in/zoom_out are slow multi-stage pinches, so they run on a daemon
        thread to keep the UI responsive. A scroll notch while a zoom is already
        in flight is dropped, so a burst of wheel events never stacks zooms.
        """
        if self._zoom_busy:
            return
        self._zoom_busy = True

        def _run() -> None:
            try:
                if direction == "in":
                    self.controller.zoom_in()
                else:
                    self.controller.zoom_out()
            except ExecutionFlag:
                pass
            except Exception as e:
                self.append_log(f"Zoom failed: {e}", "error")
            finally:
                self._zoom_busy = False

        threading.Thread(target=_run, daemon=True).start()

    def on_window_resize(self, event: object) -> None:
        on_window_resize(self, event)

    def on_log_scroll(self, event: object) -> None:
        on_log_scroll(self, event)

    def on_auto_scroll_toggle(self) -> None:
        on_auto_scroll_toggle(self)

    # =====================================================================
    # Panel toggling
    # =====================================================================

    def toggle_panel(self) -> None:
        if self.panel_visible:
            self.command_frame.grid_remove()
            self.toggle_button.configure(text="≫")
            self.main_frame.grid_columnconfigure(1, weight=0, minsize=0)
            self.main_frame.grid_columnconfigure(2, weight=1)
        else:
            self.command_frame.grid()
            self.toggle_button.configure(text="≪")
            self.main_frame.grid_columnconfigure(1, weight=0, minsize=self.panel_width)
            self.main_frame.grid_columnconfigure(2, weight=1)
        self.panel_visible = not self.panel_visible
        self.log_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

    def show_help_popup(self) -> None:
        """Show a help popup with the current command's description and parameters."""
        command_name = self.command_var.get()
        spec = get_spec(command_name)
        title = spec.title or command_name
        description = spec.description or "No description available."
        parameters = spec.param_help

        dialog = ctk.CTkToplevel()
        dialog.title(f"Help: {title}")
        dialog.geometry("480x400")
        dialog.resizable(False, False)
        dialog.configure(bg="#2b2b2b")
        dialog.grab_set()

        # Center on parent
        parent = dialog.master
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 480) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 400) // 2
        dialog.geometry(f"480x400+{x}+{y}")

        # Close on Escape
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        # Header
        header_frame = ctk.CTkFrame(dialog, fg_color="#1f1f1f", height=80)
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)

        ctk.CTkLabel(
            header_frame,
            text=title,
            font=("Arial", 20, "bold"),
            text_color="#ffffff",
            anchor="w",
        ).pack(side="left", padx=15, pady=15)

        # Content area
        content_frame = ctk.CTkFrame(dialog, fg_color="#1f1f1f")
        content_frame.pack(fill="both", expand=True, padx=20, pady=15)

        text_widget = ctk.CTkTextbox(
            content_frame,
            wrap="word",
            font=("Arial", 15),
            text_color="#cccccc",
            fg_color="#2a2a2a",
            border_width=0,
        )
        text_widget.pack(fill="both", expand=True, padx=15, pady=15)

        # Build text
        text = description
        if parameters:
            text += "\n\nParameters:\n"
            for param, desc in parameters.items():
                text += f"• {param}: {desc}\n"

        text_widget.insert("1.0", text)
        text_widget.configure(state="disabled")

        # Close button
        close_btn = ctk.CTkButton(
            dialog,
            text="Close",
            font=("Arial", 14, "bold"),
            height=40,
            width=120,
            fg_color="#3B8ED0",
            hover_color="#2d6bb0",
            command=dialog.destroy,
        )
        close_btn.pack(pady=(0, 15))

    # =====================================================================
    # Command execution
    # =====================================================================

    def on_command_change(self, command_name: str) -> None:
        if self.param_frame:
            self.param_frame.destroy()

        spec = get_spec(command_name)
        # The callback argument is only used by CommandFrame in macro mode
        # ("Add Step"); it is a no-op here in the main interface.
        self.param_frame = CommandFrame(
            self.param_container, command_name,
            spec.params,
            lambda: None,
        )
        self.param_frame.pack(expand=True, fill="both")

    def show_command_progress(self, command: str) -> None:
        """Show the label + bar inside the fixed-height progress slot.

        The slot itself is always present, so showing content here never
        resizes the preview.
        """
        self.progress_label.configure(text=f"{command} Progress:")
        self.progress_label.pack(anchor="w", padx=5, pady=(4, 0))
        self.command_progress.pack(fill="x", padx=5, pady=(2, 4))

    def hide_command_progress(self) -> None:
        self.progress_label.pack_forget()
        self.command_progress.pack_forget()

    def update_command_progress(self, progress: float) -> None:
        command = self.command_var.get()
        if self.macro_running and hasattr(self, 'current_macro_command'):
            command = self.current_macro_command

        if command not in PROGRESS_COMMANDS:
            return

        def show_progress():
            if progress == 0:
                self.show_command_progress(command)
            self.command_progress.set(progress)
            if progress >= 1:
                self.hide_command_progress()

        self.after(0, show_progress)

    def _make_macro_step_progress(self, step_index: int, total_steps: int):
        """Return a progress callback for one macro step.

        It advances the fine-grained command bar AND the macro bar within this
        step's slice, so the macro bar moves smoothly instead of jumping only
        when a step completes (which made it lag the "step n/total" log).
        """
        def callback(progress: float) -> None:
            self.update_command_progress(progress)
            clamped = max(0.0, min(1.0, float(progress)))
            macro_p = (step_index + clamped) / total_steps
            self.after(0, lambda p=macro_p: self.macro_progress.set(p))
        return callback

    def _run_thread(self, params: dict) -> None:
        self.command_running = True
        self.command_dropdown.configure(state="disabled")
        self.run_macro_btn.configure(state="disabled")
        self.macro_dropdown.configure(state="disabled")
        self.edit_macro_btn.configure(state="disabled")

        command_name = self.command_var.get()
        # A previous stop must not bleed into this run.
        self.controller.clear_cancel()
        try:
            if command_name in PROGRESS_COMMANDS:
                self.update_command_progress(0)
            spec = get_spec(command_name)
            self.append_log(f"Starting {command_name}...", "info")
            result = spec.run(self.controller, self.update_command_progress, **params)

            if result == "EXIT":
                self.append_log("Closing application...", "warning")
                self.after(1000, self.destroy)
                return

            self.append_log(f"Completed {command_name}", "success")
        except ExecutionFlag:
            self.append_log(f"Execution of {command_name} stopped", "warning")
        except AutoMonsterError as e:
            error_msg = f"Error running {command_name}: {e}"
            self.append_log(error_msg, "error")
            logging.error(error_msg)
        except Exception as e:
            error_msg = f"Error running {command_name}: {e}"
            self.append_log(error_msg, "error")
            logging.error(error_msg)
        finally:
            self.command_running = False
            self.param_frame.is_running = False
            self.param_frame.run_button.configure(text="▶ Run", fg_color=[theme.PRIMARY, theme.PRIMARY_DARK])
            self.param_frame.pause_button.configure(state="disabled")
            self.param_frame.is_paused = False
            self.param_frame.pause_button.configure(text="Pause")
            self.command_dropdown.configure(state="normal")
            if not self.macro_running:
                self.update_macro_buttons()
                self.macro_dropdown.configure(state="normal")
                self.edit_macro_btn.configure(state="normal")
            if command_name in PROGRESS_COMMANDS:
                self.hide_command_progress()

    def run_command(self) -> None:
        if not self.param_frame:
            return

        params = collect_param_values(self.param_frame.param_widgets)

        command_name = self.command_var.get()
        self.append_log(f"Running {command_name} with parameters: {params}", "debug")

        self.param_frame.pause_button.configure(state="normal")
        threading.Thread(target=self._run_thread, args=(params,), daemon=True).start()

    def stop_command(self) -> None:
        if self.controller:
            self.controller.cancel_flag = True
            logging.info(f"Set cancel_flag to True. Controller: {self.controller}")
        self.append_log("Stopping command...", "warning")

    # =====================================================================
    # Brightness
    # =====================================================================

    def lower_brightness(self) -> None:
        self.controller.lower_brightness()
        self.append_log("Lowered device brightness", "info")

    def reset_brightness(self) -> None:
        self.controller.set_auto_brightness()
        self.append_log("Reset device brightness to auto mode", "info")

    # =====================================================================
    # Debug mode
    # =====================================================================

    def toggle_debug_mode(self, event: Optional[object] = None) -> None:
        self.debug_mode = not self.debug_mode

        if self.debug_mode:
            self.screenshot_btn.pack(side="left", fill="x", expand=True, padx=(2, 1))
            self.open_sc_folder_btn.pack(side="left", fill="x", expand=True, padx=(1, 2))
            self.main_frame.grid_columnconfigure(5, weight=0, minsize=self.panel_width)
            self.debug_tool.grid(row=0, column=5, rowspan=2, padx=(0, 10), pady=10, sticky="nsew")
            self.append_log("Debug mode enabled", "debug")
        else:
            self.screenshot_btn.pack_forget()
            self.open_sc_folder_btn.pack_forget()
            self.debug_tool.grid_forget()
            self.main_frame.grid_columnconfigure(5, weight=0, minsize=0)
            self.append_log("Debug mode disabled", "success")

    # =====================================================================
    # Macros
    # =====================================================================

    def load_macros(self) -> dict:
        self.config_manager.load_configs()
        self.macro_options = self.config_manager.get_macro_options()
        return self.config_manager.get_macros()

    def run_macro(self, name: str) -> None:
        self.start_macro()

    def open_macro_dialog(self) -> None:
        dialog = MacroDialog(self, COMMANDS)
        self.wait_window(dialog)
        self.macros = self.load_macros()
        self.update_macro_list()

    def update_macro_list(self) -> None:
        self.macros = self.load_macros()
        self.macro_names = list(self.macros.keys()) if self.macros else ["No macros"]
        self.macro_dropdown.configure(values=self.macro_names)
        self.selected_macro.set(self.macro_names[0])
        self.update_macro_buttons()

    def update_macro_buttons(self) -> None:
        state = "normal" if self.macro_names != ["No macros"] else "disabled"
        self.run_macro_btn.configure(state=state)

    def toggle_macro(self) -> None:
        if not self.macro_running:
            self.start_macro()
        else:
            self.stop_macro = True
            self.controller.cancel_flag = True

    def start_temporary_macro(self, steps: list, options: dict) -> None:
        self.macro_running = True
        self.stop_macro = False
        self.run_macro_btn.configure(text="⬛ Stop Macro", fg_color=theme.DANGER)
        self.macro_dropdown.configure(state="disabled")
        self.edit_macro_btn.configure(state="disabled")
        self.command_dropdown.configure(state="disabled")
        if self.param_frame:
            self.param_frame.run_button.configure(state="disabled")

        threading.Thread(target=self._run_macro_thread, args=("Temporary Macro", steps, options), daemon=True).start()

    def start_macro(self) -> None:
        macro_name = self.selected_macro.get()
        if macro_name and macro_name != "No macros":
            self.macro_running = True
            self.stop_macro = False
            self.run_macro_btn.configure(text="⬛ Stop Macro", fg_color=theme.DANGER)
            self.macro_dropdown.configure(state="disabled")
            self.edit_macro_btn.configure(state="disabled")
            self.command_dropdown.configure(state="disabled")
            if self.param_frame:
                self.param_frame.run_button.configure(state="disabled")

            threading.Thread(target=self._run_macro_thread, args=(macro_name,), daemon=True).start()

    def _run_macro_thread(self, name: str, steps: Optional[list] = None, options: Optional[dict] = None) -> None:
        try:
            macro_steps = steps if steps is not None else self.macros[name]
            current_options = options if options is not None else self.macro_options

            self.after(0, lambda: [
                self.macro_progress.grid(),
                self.macro_progress.set(0)
            ])
            total_steps = len(macro_steps)

            # A previous stop must not bleed into this run.
            self.controller.clear_cancel()

            lowered_brightness = False
            if current_options.get("lower_brightness", False):
                lowered_brightness = True
                self.append_log("Lowering brightness before macro execution", "info")
                self.controller.lower_brightness()

            for i, step in enumerate(macro_steps):
                if self.stop_macro:
                    self.append_log("Macro execution stopped by user", "warning")
                    break

                command = step["command"]
                self.current_macro_command = command
                params = step["params"]
                spec = get_spec(command)
                try:
                    self.append_log(f"Running macro step: {command} ({i+1}/{total_steps})", "info")

                    if command in PROGRESS_COMMANDS:
                        self.update_command_progress(0)
                        progress_cb = self._make_macro_step_progress(i, total_steps)
                    else:
                        progress_cb = self.update_command_progress

                    result = spec.run(self.controller, progress_cb, **params)

                    if result == "EXIT":
                        self.append_log("Closing application...", "warning")
                        self.after(1000, self.destroy)
                        return

                    if command in PROGRESS_COMMANDS:
                        self.after(0, self.hide_command_progress)

                    progress = (i + 1) / total_steps
                    self.after(0, lambda p=progress: self.macro_progress.set(p))
                except ExecutionFlag:
                    self.append_log(f"Macro step {command} stopped", "warning")
                    break
                except Exception as e:
                    self.append_log(f"Error in macro step {command}: {str(e)}", "error")
                    break

            if not self.stop_macro and current_options.get("lock_device", False):
                self.append_log("Locking device after macro completion", "info")
                self.controller.lock_device()

            if lowered_brightness:
                self.controller._reset_brightness_if_lowered()

        finally:
            if hasattr(self, 'current_macro_command'):
                delattr(self, 'current_macro_command')

            self.macro_running = False
            self.stop_macro = False
            self.run_macro_btn.configure(text="▶ Run Macro", fg_color=[theme.PRIMARY, theme.PRIMARY_DARK])
            self.macro_dropdown.configure(state="normal")
            self.edit_macro_btn.configure(state="normal")
            self.macro_progress.grid_remove()
            if not self.command_running:
                self.command_dropdown.configure(state="normal")
                if self.param_frame:
                    self.param_frame.run_button.configure(state="normal")

    def run_selected_macro(self) -> None:
        macro_name = self.selected_macro.get()
        if macro_name and macro_name != "No macros":
            self.run_macro(macro_name)

    # =====================================================================
    # Cleanup
    # =====================================================================

    def _on_close(self) -> None:
        """Explicit window close: stop the device stream, then destroy."""
        controller = getattr(self, "controller", None)
        if controller is not None:
            try:
                controller.client.remove_listener(amscrcpy.EVENT_FRAME)
                controller.client.stop()
            except Exception:
                # Ignore errors during cleanup
                pass
        self.destroy()

    def open_screenshots_folder(self) -> None:
        try:
            sc_dir = self.controller._sc_dir()
            if not sc_dir.exists():
                sc_dir.mkdir(exist_ok=True)

            if os.name == 'nt':
                os.startfile(str(sc_dir))
            elif os.name == 'posix':
                subprocess.run(
                    ['open' if sys.platform == 'darwin' else 'xdg-open', str(sc_dir)]
                )

            self.append_log("Opened screenshots folder", "info")
        except Exception as e:
            self.append_log(f"Error opening folder: {str(e)}", "error")
