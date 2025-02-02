import customtkinter as ctk
import json
import os
from command_frame import CommandFrame

DEFAULT_MACROS_FILE = "macros.json"

class MacroDialog(ctk.CTkToplevel):
    def __init__(self, parent, commands):
        super().__init__(parent)
        self.title("Macro Manager")
        self.parent = parent
        self.commands = commands
        self.macros = self.load_macros()
        self.param_widgets = {}  # Initialize param_widgets dictionary
        
        # Make dialog modal
        self.transient(parent)  # Set parent-child relationship
        self.grab_set()  # Make window modal
        
        # Set size and make non-resizable
        self.geometry("800x600")
        self.resizable(False, False)
        
        # Create main layout
        self.create_widgets()
        
        # Center relative to parent
        self.center_dialog()
        
        # Wait for window to be closed
        self.wait_window()
        
    def center_dialog(self):
        """Center the dialog relative to its parent"""
        self.update_idletasks()
        
        # Get parent and dialog geometries
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        
        # Calculate centered position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f'+{x}+{y}')

    def create_widgets(self):
        # Create left and right panes
        left_frame = ctk.CTkFrame(self)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        right_frame = ctk.CTkFrame(self)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Left pane - Macro selection and management
        macro_label = ctk.CTkLabel(left_frame, text="Macro List", font=("Arial", 16, "bold"))
        macro_label.pack(pady=(10, 5))

        # Macro selection dropdown - updated logic
        self.macro_names = list(self.macros.keys())
        if not self.macro_names:
            self.macro_names = ["No macros"]
        
        self.selected_macro = ctk.StringVar(value=self.macro_names[0])
        self.macro_dropdown = ctk.CTkOptionMenu(
            left_frame,
            values=self.macro_names,
            variable=self.selected_macro,
            command=self.on_macro_selected,
            width=220
        )
        self.macro_dropdown.pack(pady=10)

        # Update button states based on macro existence
        self.btn_frame = ctk.CTkFrame(left_frame)
        self.btn_frame.pack(fill="x", pady=10)

        self.delete_btn = ctk.CTkButton(self.btn_frame, text="Delete", command=self.delete_macro)
        self.run_btn = ctk.CTkButton(self.btn_frame, text="Run", command=self.run_macro)
        
        ctk.CTkButton(self.btn_frame, text="New", command=self.new_macro).pack(side="left", expand=True, padx=5)
        self.delete_btn.pack(side="left", expand=True, padx=5)
        self.run_btn.pack(side="left", expand=True, padx=5)
        
        self.update_button_states()

        # Right pane - Step configuration
        step_label = ctk.CTkLabel(right_frame, text="Steps Configuration", font=("Arial", 16, "bold"))
        step_label.pack(pady=(10, 5))

        # Add command selection dropdown
        cmd_frame = ctk.CTkFrame(right_frame)
        cmd_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(cmd_frame, text="Command:").pack(side="left", padx=5)
        self.command_var = ctk.StringVar(value=next(iter(self.commands)))
        self.command_dropdown = ctk.CTkOptionMenu(
            cmd_frame,
            values=list(self.commands.keys()),
            variable=self.command_var,
            command=self.on_command_changed
        )
        self.command_dropdown.pack(side="left", expand=True, padx=5)

        # Command frame container
        self.command_container = ctk.CTkFrame(right_frame)
        self.command_container.pack(fill="both", expand=True, pady=10, padx=10)

        # Create the initial command frame
        self.update_command_frame(next(iter(self.commands)))

        # Steps list
        steps_label = ctk.CTkLabel(right_frame, text="Macro Steps:", font=("Arial", 14, "bold"))
        steps_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.steps_text = ctk.CTkTextbox(right_frame, height=200)
        self.steps_text.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        self.steps_text.configure(state="disabled")

        # Bottom buttons
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        ctk.CTkButton(
            bottom_frame,
            text="Save & Close",
            command=self.save_and_close
        ).pack(side="right", padx=5)

    def update_button_states(self):
        """Enable/disable buttons based on macro existence"""
        has_macros = self.macro_names != ["No macros"]
        state = "normal" if has_macros else "disabled"
        self.delete_btn.configure(state=state)
        self.run_btn.configure(state=state)

    def new_macro(self):
        dialog = ctk.CTkInputDialog(text="Enter macro name:", title="New Macro")
        name = dialog.get_input()
        if name:
            if self.macro_names == ["No macros"]:
                self.macro_names = []
            self.macros[name] = []
            self.macro_names.append(name)
            self.macro_dropdown.configure(values=self.macro_names)
            self.selected_macro.set(name)
            self.update_button_states()
            self.on_macro_selected(name)

    def delete_macro(self):
        name = self.selected_macro.get()
        if name and name in self.macros:
            del self.macros[name]
            self.macro_names.remove(name)
            if not self.macro_names:
                self.macro_names = ["No macros"]
                self.delete_btn.configure(state="disabled")
                self.run_btn.configure(state="disabled")
            self.macro_dropdown.configure(values=self.macro_names)
            self.selected_macro.set(self.macro_names[0])
            self.update_button_states()
            self.on_macro_selected(self.selected_macro.get())

    def run_macro(self):
        name = self.selected_macro.get()
        if name and name in self.macros:
            self.parent.run_macro(name)
            self.destroy()

    def on_macro_selected(self, name):
        self.steps_text.configure(state="normal")
        self.steps_text.delete("1.0", "end")
        if name in self.macros:
            for step in self.macros[name]:
                self.steps_text.insert("end", f"{step['command']} - {step['params']}\n")
        self.steps_text.configure(state="disabled")

    def on_command_changed(self, command_name):
        self.update_command_frame(command_name)

    def update_command_frame(self, command_name):
        # Clear existing command frame
        for widget in self.command_container.winfo_children():
            widget.destroy()

        # Create new command frame
        self.current_command_frame = CommandFrame(
            self.command_container,
            command_name,
            self.commands[command_name],
            self.add_step,
            mode="macro"
        )
        self.current_command_frame.pack(fill="both", expand=True)

    def add_step(self):
        name = self.selected_macro.get()
        if name and name in self.macros:
            command = self.command_var.get()
            params = self.current_command_frame.get_current_params()
            
            self.macros[name].append({"command": command, "params": params})
            self.on_macro_selected(name)  # Refresh steps display

    def save_and_close(self):
        with open(DEFAULT_MACROS_FILE, "w") as f:
            json.dump(self.macros, f, indent=4)
        self.destroy()

    def load_macros(self):
        if os.path.isfile(DEFAULT_MACROS_FILE):
            with open(DEFAULT_MACROS_FILE, "r") as f:
                return json.load(f)
        return {}