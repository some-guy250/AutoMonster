import sys
from gui import ControllerGUI
from tkinter import messagebox

def main():
    try:
        # Check if app was launched after update
        updated = len(sys.argv) > 1 and sys.argv[1] == "updated"
        
        app = ControllerGUI()
        if app.all_good:
            app.mainloop()
    except Exception as e:
        messagebox.showerror("Error", str(e))

if __name__ == '__main__':
    main()
