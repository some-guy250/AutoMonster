import json
import logging
import os
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Valid macro option keys
VALID_MACRO_OPTIONS = {"lower_brightness", "lock_device"}

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
        self.defaults = self._load_and_validate_defaults()
        
        if os.path.isfile(self.MACROS_FILE):
            self.macros, self.macro_options = self._load_and_validate_macros()
        else:
            self.macros = {}
            self.macro_options = {}

    def _load_and_validate_defaults(self) -> Dict[str, Any]:
        """Load defaults.json with validation."""
        if not os.path.exists(self.DEFAULTS_FILE):
            logger.warning(f"Defaults file not found: {self.DEFAULTS_FILE}")
            return {}
        
        try:
            with open(self.DEFAULTS_FILE, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.DEFAULTS_FILE}: {e}")
            return {}
        
        # Validate structure
        if not isinstance(data, dict):
            logger.error(f"Defaults file must contain a JSON object, got {type(data).__name__}")
            return {}
        
        # Validate each command's parameters
        valid_defaults = {}
        for cmd_name, params in data.items():
            if not isinstance(params, dict):
                logger.warning(f"Skipping invalid command '{cmd_name}': expected dict, got {type(params).__name__}")
                continue
            
            valid_params = {}
            for param_name, value in params.items():
                # Validate values
                if isinstance(value, bool):
                    valid_params[param_name] = value
                elif isinstance(value, (int, float)):
                    valid_params[param_name] = value
                elif isinstance(value, str):
                    valid_params[param_name] = value
                elif isinstance(value, list):
                    # Lists are valid (e.g., Cavern.caverns)
                    valid_params[param_name] = value
                else:
                    logger.warning(f"Skipping invalid value for {cmd_name}.{param_name}: {type(value).__name__}")
            
            valid_defaults[cmd_name] = valid_params
        
        return valid_defaults

    def _load_and_validate_macros(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Load macros.json with validation."""
        try:
            with open(self.MACROS_FILE, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.MACROS_FILE}: {e}")
            return {}, {}
        
        if not isinstance(data, dict):
            logger.error(f"Macros file must contain a JSON object, got {type(data).__name__}")
            return {}, {}
        
        # Extract macros
        macros = data.get("macros", {})
        if not isinstance(macros, dict):
            logger.error(f"Macros must be a dict, got {type(macros).__name__}")
            return {}, {}
        
        # Extract and validate options
        options = data.get("options", {})
        if not isinstance(options, dict):
            logger.warning(f"Macro options must be a dict, got {type(options).__name__}")
            options = {}
        else:
            # Filter to only valid option keys
            valid_options = {}
            for key, value in options.items():
                if key in VALID_MACRO_OPTIONS:
                    if isinstance(value, bool):
                        valid_options[key] = value
                    else:
                        logger.warning(f"Option '{key}' must be boolean, got {type(value).__name__}")
                else:
                    logger.warning(f"Unknown macro option: '{key}'")
            options = valid_options
        
        return macros, options

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
