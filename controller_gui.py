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
import scrcpy

from utils.AutoMonsterErrors import *
from AutoMonster import Controller
from gui.gui_config import GUI_COMMANDS, GUI_COMMAND_DESCRIPTIONS
from gui.command_frame import CommandFrame
from gui.device_selection_frame import DeviceSelectionFrame
from gui.macro_dialog import MacroDialog
from utils.config_manager import ConfigManager
from gui.gui_frames import build_main_interface, _show_update_message_dialog
from gui.gui_events import (
    update_image, update_image_safe,
    on_mouse_down, on_mouse_move, on_mouse_up,
    on_window_resize, on_log_scroll, on_auto_scroll_toggle,
)

if os.path.isfile("version.txt"):
    with open("version.txt", "r") as file:
        __version__ = file.read().strip()


class ControllerGUI(ctk.CTk):
    def __init__(self, update_message: str = "") -> None:
        super().__init__()

        self.update_message = update_message

        if os.path.exists("asset_images/favicon.ico"):
            self.iconbitmap("asset_images/favicon.ico")

        self.title("AutoMonster")
        self.minsize(400, 450)
        self.resizable(False, False)

        self.config_manager = ConfigManager()
        self.macros = self.config_manager.get_macros()
        self.macro_options = self.config_manager.get_macro_options()
        self.commands = GUI_COMMANDS
        self.command_descriptions = GUI_COMMAND_DESCRIPTIONS

        self.macro_running = False
        self.stop_macro = False
        self.command_running = False

        self.device_frame = DeviceSelectionFrame(self, self.on_device_selected)
        self.main_frame = ctk.CTkFrame(self)

        self.show_device_selection()

    # =====================================================================
    # Device selection
    # =====================================================================

    def show_device_selection(self) -> None:
        self.main_frame.pack_forget()
        self.device_frame.pack(expand=True, fill="both", padx=20, pady=20)
        self.center_window()

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
        self.last_check_battery = datetime.now()
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
        for cmd_name, params in self.commands.items():
            saved = loaded_defaults.get(cmd_name, {})
            for param_name, config in params.items():
                if param_name in saved:
                    config["default"] = saved[param_name]

    # =====================================================================
    # Logging
    # =====================================================================

    def append_log(self, message: str, level: str = "info") -> None:
        if level == "debug" and not self.debug_mode:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert("end", log_entry, level)
        if self.auto_scroll.get():
            self.log_text.see("end")

    # =====================================================================
    # Event handler wrappers (delegate to gui_events module)
    # =====================================================================

    def update_image(self, frame: np.ndarray) -> None:
        update_image(self, frame)

    def update_image_safe(self, frame: np.ndarray) -> None:
        update_image_safe(self, frame)

    def on_mouse_down(self, event: object) -> None:
        on_mouse_down(self, event)

    def on_mouse_move(self, event: object) -> None:
        on_mouse_move(self, event)

    def on_mouse_up(self, event: object) -> None:
        on_mouse_up(self, event)

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

    def toggle_info_panel(self) -> None:
        if self.info_visible:
            self.info_frame.grid_forget()
            self.info_toggle_button.configure(text="≪")
            self.main_frame.grid_columnconfigure(3, weight=0, minsize=0)
            self.main_frame.grid_columnconfigure(2, weight=1)
        else:
            self.info_frame.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")
            self.info_toggle_button.configure(text="≫")
            self.main_frame.grid_columnconfigure(3, weight=0, minsize=self.panel_width)
            self.main_frame.grid_columnconfigure(2, weight=1)
        self.info_visible = not self.info_visible

    def update_info_panel(self, command_name: str) -> None:
        info = self.command_descriptions.get(command_name, {})
        self.info_title.configure(text=info.get("title", command_name))
        self.info_description.configure(state="normal")
        self.info_description.delete("1.0", "end")

        description = info.get("description", "No description available.")
        parameters = info.get("parameters", {})

        text = f"{description}\n\n"
        if parameters:
            text += "Parameters:\n"
            for param, desc in parameters.items():
                text += f"• {param}: {desc}\n"

        self.info_description.insert("1.0", text)
        self.info_description.configure(state="disabled")

    # =====================================================================
    # Command execution
    # =====================================================================

    def on_command_change(self, command_name: str) -> None:
        if self.param_frame:
            self.param_frame.destroy()

        self.param_frame = CommandFrame(
            self.param_container, command_name,
            self.commands[command_name],
            self.get_command_callback(command_name)
        )
        self.param_frame.pack(expand=True, fill="both")
        self.update_info_panel(command_name)

    def get_command_callback(self, command_name: str) -> Callable[..., Optional[str]]:
        if command_name == "PVP":
            return lambda **kwargs: self.controller.do_pvp(
                kwargs.pop("num_battles", 2), kwargs.pop("handle_boxes", True),
                kwargs.pop("reduce_box_time", True),
                progress_callback=self.update_command_progress
            )
        elif command_name == "Era Saga":
            return self.controller.do_era_saga
        elif command_name == "Resource Dungeons":
            return lambda **kwargs: self.controller.do_resource_dungeons(
                wait_for_stamina_to_refill=kwargs.pop("wait_for_stamina", False)
            )
        elif command_name == "Ads":
            return self.controller.play_ads
        elif command_name == "Reduce Time":
            return lambda **kwargs: self.controller.reduce_time(
                kwargs.pop("number_of_ads", 3)
            )
        elif command_name == "Cavern":
            return lambda **kwargs: self.controller.do_cavern(
                *kwargs.pop("caverns", []), max_rooms=kwargs.pop("max_rooms", 3),
                change_team=kwargs.pop("change_team", True),
                progress_callback=self.update_command_progress
            )
        elif command_name == "Breed Monsters":
            return lambda **kwargs: self.controller.breed_monsters(
                kwargs.pop("num_breeds", 1), kwargs.pop("use_tree", False),
                kwargs.pop("feed_and_sell_monsters", False), kwargs.pop("sell", False),
                batch_size=kwargs.pop("batch_size", 15),
                progress_callback=self.update_command_progress
            )
        elif command_name == "Feed and Sell Monsters":
            return lambda **kwargs: self.controller.feed_and_sell_monsters()
        elif command_name == "Craft Runes":
            return lambda **kwargs: self.controller.craft_runes(
                kwargs.pop("num_runes", 10),
                kwargs.pop("level", "I"),
                kwargs.pop("rune_type", "Life"),
                kwargs.pop("team", False),
                progress_callback=self.update_command_progress
            )
        elif command_name == "Close Game":
            return lambda **kwargs: self.controller.close_game(
                action=kwargs.pop("action", "Close Game Only")
            )
        else:
            raise ValueError(f"Unknown command: {command_name}")

    def update_command_progress(self, progress: float) -> None:
        command = self.command_var.get()
        if self.macro_running and hasattr(self, 'current_macro_command'):
            command = self.current_macro_command

        if command not in ["PVP", "Cavern", "Breed Monsters"]:
            return

        def show_progress():
            if progress == 0:
                self.progress_label.configure(text=f"{command} Progress:")
                self.progress_frame.pack(fill="x", padx=5, pady=(5, 0))
                self.progress_frame.update()
                self.command_progress.update()
            self.command_progress.set(progress)
            self.command_progress.update()
            if progress >= 1:
                self.progress_frame.pack_forget()

        self.after(0, show_progress)

    def _run_thread(self, params: dict) -> None:
        self.command_running = True
        self.command_dropdown.configure(state="disabled")
        self.run_macro_btn.configure(state="disabled")
        self.macro_dropdown.configure(state="disabled")
        self.edit_macro_btn.configure(state="disabled")

        command_name = self.command_var.get()
        try:
            if command_name in ["PVP", "Cavern", "Breed Monsters"]:
                self.update_command_progress(0)
            if self.param_frame and hasattr(self.param_frame, 'progress'):
                self.param_frame.progress.set(0)
            callback = self.get_command_callback(command_name)
            self.append_log(f"Starting {command_name}...", "info")
            result = callback(**params)

            if result == "EXIT":
                self.append_log("Closing application...", "warning")
                self.after(1000, self.destroy)
                return

            self.append_log(f"Completed {command_name}", "success")
        except AutoMonsterError as e:
            error_msg = f"Error running {command_name}: {e}"
            self.append_log(error_msg, "error")
            logging.error(error_msg)
        except Exception as e:
            error_msg = f"Error running {command_name}: {e}"
            self.append_log(error_msg, "error")
            logging.error(error_msg)
        except  ExecutionFlag:
            self.append_log(f"Execution of {command_name} stopped", "warning")
        finally:
            self.command_running = False
            self.param_frame.is_running = False
            self.param_frame.run_button.configure(text="▶ Run", fg_color=["#3B8ED0", "#1F6AA5"])
            self.param_frame.pause_button.configure(state="disabled")
            self.param_frame.is_paused = False
            self.param_frame.pause_button.configure(text="Pause")
            self.command_dropdown.configure(state="normal")
            if not self.macro_running:
                self.update_macro_buttons()
                self.macro_dropdown.configure(state="normal")
                self.edit_macro_btn.configure(state="normal")
            if command_name in ["PVP", "Cavern", "Breed Monsters"]:
                self.progress_frame.pack_forget()

    def run_command(self) -> None:
        if not self.param_frame:
            return

        params = {}
        for param_name, widget in self.param_frame.param_widgets.items():
            if isinstance(widget, ctk.CTkSlider):
                params[param_name] = int(widget.get())
            elif isinstance(widget, ctk.CTkCheckBox):
                params[param_name] = bool(widget.get())
            elif isinstance(widget, ctk.CTkOptionMenu):
                params[param_name] = widget.get()
            elif isinstance(widget, list):
                selected = [choice for choice, var in widget if var.get()]
                params[param_name] = selected

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
        dialog = MacroDialog(self, self.commands)
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
        self.run_macro_btn.configure(text="⬛ Stop Macro", fg_color="red")
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
            self.run_macro_btn.configure(text="⬛ Stop Macro", fg_color="red")
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
                self.macro_progress.pack(fill="x", padx=5, pady=(5, 0)),
                self.macro_progress.set(0)
            ])
            total_steps = len(macro_steps)

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
                callback = self.get_command_callback(command)
                if callback:
                    try:
                        self.append_log(f"Running macro step: {command} ({i+1}/{total_steps})", "info")

                        if command in ["PVP", "Cavern", "Breed Monsters"]:
                            self.update_command_progress(0)

                        result = callback(**params)

                        if result == "EXIT":
                            self.append_log("Closing application...", "warning")
                            self.after(1000, self.destroy)
                            return

                        if command in ["PVP", "Cavern", "Breed Monsters"]:
                            self.after(0, self.progress_frame.pack_forget)

                        progress = (i + 1) / total_steps
                        self.after(0, lambda p=progress: [
                            self.macro_progress.set(p), self.macro_progress.update()
                        ])
                    except  ExecutionFlag:
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
            self.run_macro_btn.configure(text="▶ Run Macro", fg_color=["#3B8ED0", "#1F6AA5"])
            self.macro_dropdown.configure(state="normal")
            self.edit_macro_btn.configure(state="normal")
            self.macro_progress.pack_forget()
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

    def __del__(self):
        controller = getattr(self, "controller", None)
        if controller is not None:
            try:
                controller.client.remove_listener(scrcpy.EVENT_FRAME)
                controller.client.stop()
            except Exception:
                # Ignore errors during cleanup
                pass

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
