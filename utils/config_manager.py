import json
import logging
import os
from typing import Dict, Any, Optional

class ConfigManager:
    _instance = None
    DEFAULTS_FILE = "defaults.json"
    MACROS_FILE = "macros.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.defaults = {}
            cls._instance.macros = {}
            cls._instance.macro_options = {}
            cls._instance.load_configs()
        return cls._instance

    def load_configs(self):
        self.defaults = self._load_json(self.DEFAULTS_FILE)
        
        if os.path.isfile(self.MACROS_FILE):
            with open(self.MACROS_FILE, "r") as f:
                data = json.load(f)
                self.macros = data.get("macros", {})
                self.macro_options = data.get("options", {})
        else:
            self.macros = {}
            self.macro_options = {}

    def _load_json(self, filename: str) -> Dict[str, Any]:
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Error loading {filename}: {e}")
        return {}

    def get_default(self, key: str, default_val=None):
        return self.defaults.get(key, default_val)

    def get_macros(self):
        return self.macros
    
    def get_macro_options(self):
        return self.macro_options
    
    def save_macros(self, macros: Dict, options: Optional[Dict] = None):
        self.macros = macros
        if options is not None:
            self.macro_options = options
            
        data = {
            "macros": self.macros,
            "options": self.macro_options
        }
        with open(self.MACROS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
