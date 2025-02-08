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
        
        # Initialize first macro's steps display
        if self.macro_names and self.macro_names[0] != "No macros":
            self.on_macro_selected(self.macro_names[0])

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
        # Top frame for macro selection and management
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        # Macro selection section
        macro_label = ctk.CTkLabel(top_frame, text="Select Macro:", font=("Arial", 12))
        macro_label.pack(side="left", padx=5)

        self.macro_names = list(self.macros.keys())
        if not self.macro_names:
            self.macro_names = ["No macros"]
        
        self.selected_macro = ctk.StringVar(value=self.macro_names[0])
        self.macro_dropdown = ctk.CTkOptionMenu(
            top_frame,
            values=self.macro_names,
            variable=self.selected_macro,
            command=self.on_macro_selected,
            width=300
        )
        self.macro_dropdown.pack(side="left", padx=5)

        # Buttons frame
        buttons_frame = ctk.CTkFrame(top_frame)
        buttons_frame.pack(side="right", padx=5)

        ctk.CTkButton(
            buttons_frame, 
            text="New Macro", 
            command=self.new_macro,
            width=100
        ).pack(side="left", padx=5)

        self.delete_btn = ctk.CTkButton(
            buttons_frame, 
            text="Delete Macro", 
            command=self.delete_macro,
            width=100
        )
        self.delete_btn.pack(side="left", padx=5)

        # Split into left and right panes
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Left pane - Command configuration
        left_pane = ctk.CTkFrame(content_frame)
        left_pane.pack(side="left", fill="both", expand=True, padx=(0, 5))

        command_label = ctk.CTkLabel(left_pane, text="Command Configuration", font=("Arial", 14, "bold"))
        command_label.pack(anchor="w", pady=5, padx=10)

        # Command selection - now in its own row with full width
        cmd_label = ctk.CTkLabel(left_pane, text="Command:", anchor="w")
        cmd_label.pack(fill="x", pady=(5,0), padx=10)
        
        self.command_var = ctk.StringVar(value=next(iter(self.commands)))
        self.command_dropdown = ctk.CTkOptionMenu(
            left_pane,
            values=list(self.commands.keys()),
            variable=self.command_var,
            command=self.on_command_changed,
            width=300  # Fixed width for consistency
        )
        self.command_dropdown.pack(fill="x", pady=(0,5), padx=10)

        # Command configuration container
        self.command_container = ctk.CTkFrame(left_pane)
        self.command_container.pack(fill="both", expand=True, pady=5, padx=10)

        # Right pane - Steps list with side buttons
        right_pane = ctk.CTkFrame(content_frame)
        right_pane.pack(side="right", fill="both", expand=True, padx=(5, 0))

        steps_label = ctk.CTkLabel(right_pane, text="Macro Steps", font=("Arial", 14, "bold"))
        steps_label.pack(anchor="w", pady=5, padx=10)

        # Create horizontal container for steps and buttons
        steps_container = ctk.CTkFrame(right_pane)
        steps_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Steps list with selection capability
        self.steps_list = ctk.CTkTextbox(steps_container, height=400)
        self.steps_list.pack(side="left", fill="both", expand=True)
        self.steps_list.bind("<Button-1>", self.on_step_click)

        # Vertical buttons frame
        buttons_frame = ctk.CTkFrame(steps_container)
        buttons_frame.pack(side="right", fill="y", padx=(5, 0))

        # Add move up/down and remove buttons vertically
        self.move_up_btn = ctk.CTkButton(
            buttons_frame,
            text="▲",
            command=self.move_step_up,
            width=30,
            height=30,
            font=("Arial", 14),
            state="disabled"
        )
        self.move_up_btn.pack(pady=(0, 2))

        self.move_down_btn = ctk.CTkButton(
            buttons_frame,
            text="▼",
            command=self.move_step_down,
            width=30,
            height=30,
            font=("Arial", 14),
            state="disabled"
        )
        self.move_down_btn.pack(pady=(0, 10))

        self.remove_step_btn = ctk.CTkButton(
            buttons_frame,
            text="✕",  # Unicode X symbol
            command=self.remove_selected_step,
            width=30,
            height=30,
            font=("Arial", 14),
            state="disabled"
        )
        self.remove_step_btn.pack()

        # Bottom frame with save button
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(
            bottom_frame,
            text="Save & Close",
            command=self.save_and_close
        ).pack(side="right", padx=5)

        # Create the initial command frame
        self.update_command_frame(next(iter(self.commands)))
        self.update_button_states()
        
        # Initialize step selection tracking
        self.selected_step_index = None

    def update_step_buttons(self):
        """Update the state of step manipulation buttons"""
        macro_name = self.selected_macro.get()
        if self.selected_step_index is not None and macro_name in self.macros:
            total_steps = len(self.macros[macro_name])
            # Enable/disable buttons based on position
            self.remove_step_btn.configure(state="normal")
            self.move_up_btn.configure(state="normal" if self.selected_step_index > 0 else "disabled")
            self.move_down_btn.configure(state="normal" if self.selected_step_index < total_steps - 1 else "disabled")
        else:
            # Disable all buttons if no step is selected
            self.remove_step_btn.configure(state="disabled")
            self.move_up_btn.configure(state="disabled")
            self.move_down_btn.configure(state="disabled")

    def move_step_up(self):
        if self.selected_step_index is not None and self.selected_step_index > 0:
            macro_name = self.selected_macro.get()
            if macro_name in self.macros:
                # Swap steps
                steps = self.macros[macro_name]
                steps[self.selected_step_index], steps[self.selected_step_index - 1] = \
                    steps[self.selected_step_index - 1], steps[self.selected_step_index]
                # Update selection
                self.selected_step_index -= 1
                # Refresh display
                self.on_macro_selected(macro_name)
                # Reselect the moved step
                self.select_step(self.selected_step_index)

    def move_step_down(self):
        macro_name = self.selected_macro.get()
        if self.selected_step_index is not None and macro_name in self.macros:
            if self.selected_step_index < len(self.macros[macro_name]) - 1:
                # Swap steps
                steps = self.macros[macro_name]
                steps[self.selected_step_index], steps[self.selected_step_index + 1] = \
                    steps[self.selected_step_index + 1], steps[self.selected_step_index]
                # Update selection
                self.selected_step_index += 1
                # Refresh display
                self.on_macro_selected(macro_name)
                # Reselect the moved step
                self.select_step(self.selected_step_index)

    def select_step(self, index):
        """Helper method to select a step and highlight it"""
        if index is not None:
            self.selected_step_index = index
            # Clear previous selection
            self.steps_list._textbox.tag_remove("selected", "1.0", "end")
            # Add new selection
            line_start = f"{index + 1}.0"
            line_end = f"{index + 2}.0"
            self.steps_list._textbox.tag_add("selected", line_start, line_end)
            self.steps_list._textbox.tag_configure("selected", background="#2f6f96")
            # Update button states
            self.update_step_buttons()

    def on_step_click(self, event):
        if self.selected_macro.get() == "No macros":
            return

        # Get click position and calculate actual line number (0-based)
        index = self.steps_list.index(f"@{event.x},{event.y}")
        line = int(float(index)) - 1  # Subtract 1 to convert to 0-based index
        
        # Verify the line is within bounds of current macro
        macro_name = self.selected_macro.get()
        if macro_name in self.macros and 0 <= line < len(self.macros[macro_name]):
            self.select_step(line)
        else:
            self.select_step(None)

    def remove_selected_step(self):
        if self.selected_step_index is not None:
            macro_name = self.selected_macro.get()
            if macro_name in self.macros and 0 <= self.selected_step_index < len(self.macros[macro_name]):
                # Remove the step from the macro
                self.macros[macro_name].pop(self.selected_step_index)
                # Reset selection
                self.selected_step_index = None
                self.remove_step_btn.configure(state="disabled")
                # Update display
                self.on_macro_selected(macro_name)

    def format_step(self, step):
        """Format a step into a readable string"""
        command = step['command']
        params = step['params']
        
        # If no parameters, just show the command
        if not params:
            return command
        
        # Format parameters based on their type
        param_parts = []
        for key, value in params.items():
            # Format lists/arrays
            if isinstance(value, (list, tuple)):
                if value:  # Only show if not empty
                    formatted_value = ', '.join(str(v) for v in value)
                    param_parts.append(f"{key}: [{formatted_value}]")
            # Format booleans
            elif isinstance(value, bool):
                if value:  # Only show enabled options
                    param_parts.append(key)
            # Format other values (numbers, strings)
            elif value is not None and value != "":
                param_parts.append(f"{key}: {value}")
        
        # Combine command with parameters
        if param_parts:
            return f"{command} ({'; '.join(param_parts)})"
        return command

    def on_macro_selected(self, name):
        # Clear any existing selection first
        self.selected_step_index = None
        self.update_step_buttons()
        self.steps_list._textbox.tag_remove("selected", "1.0", "end")
        
        self.steps_list.configure(state="normal")
        self.steps_list.delete("1.0", "end")
        if name in self.macros:
            # Format each step
            for i, step in enumerate(self.macros[name], 1):
                formatted_step = self.format_step(step)
                self.steps_list.insert("end", f"{i}. {formatted_step}\n")
        self.steps_list.configure(state="disabled")
        # Reset step selection
        self.selected_step_index = None
        self.remove_step_btn.configure(state="disabled")

    def update_button_states(self):
        """Enable/disable buttons based on macro existence"""
        has_macros = self.macro_names != ["No macros"]
        state = "normal" if has_macros else "disabled"
        self.delete_btn.configure(state=state)

    def center_input_dialog(self, dialog):
        """Center the input dialog relative to the macro dialog"""
        # Wait for dialog to be created
        dialog.wait_visibility()
        
        # Get macro dialog and input dialog geometries
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_width = self.winfo_width()
        main_height = self.winfo_height()
        
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()
        
        # Calculate centered position
        x = main_x + (main_width - dialog_width) // 2
        y = main_y + (main_height - dialog_height) // 2
        
        dialog.geometry(f'+{x}+{y}')

    def new_macro(self):
        dialog = ctk.CTkInputDialog(text="Enter macro name:", title="New Macro")
        self.center_input_dialog(dialog)
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
            self.macro_dropdown.configure(values=self.macro_names)
            self.selected_macro.set(self.macro_names[0])
            self.update_button_states()
            self.on_macro_selected(self.selected_macro.get())

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
        self.destroy()  # Only destroy the dialog window, don't quit the application

    def load_macros(self):
        if os.path.isfile(DEFAULT_MACROS_FILE):
            with open(DEFAULT_MACROS_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_macros(self):
        """Persist macros to JSON file."""
        with open(DEFAULT_MACROS_FILE, "w") as f:
            json.dump(self.macros, f, indent=4)

    def add_step_to_macro(self, macro_name, command, params):
        """Append a step with command and parameters."""
        if macro_name in self.macros:
            self.macros[macro_name].append({"command": command, "params": params})
            self.save_macros()

    def update_macro(self, name, new_steps):
        """Replace macro steps."""
        if name in self.macros:
            self.macros[name] = new_steps
            self.save_macros()