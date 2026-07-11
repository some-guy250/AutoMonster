# =============================================================================
# GUI command definitions and descriptions
# =============================================================================

GUI_COMMANDS = {
    "Resource Dungeons": {
        "wait_for_stamina": {"type": "bool", "default": False}
    },
    "Ads": {},
    "Reduce Time": {
        "number_of_ads": {"type": "int", "min": 1, "max": 4, "default": 4}
    },
    "Cavern": {
        "caverns": {
            "type": "multiple_choice",
            "tabs": {
                "Ancestral": [
                    "evaris",
                    "geneza",
                    "jestin",
                    "baba",
                    "khalorc",
                    "tyr",
                    "robur",
                    "theton",
                    "griffania"
                ],
                "Era": [
                    "misery",
                    "conspiracy",
                    "feral",
                    "historia",
                    "multiverse",
                    "alpine",
                    "abyssal",
                    "galactic",
                    "blossom",
                    "doomed",
                    "metro",
                    "corrupted",
                    "cosmic",
                    "original"
                ]
            },
            "default": []
        },
        "max_rooms": {"type": "int", "min": 1, "max": 5, "default": 3},
        "change_team": {"type": "bool", "default": True}
    },
    "PVP": {
        "num_battles": {"type": "int", "min": 1, "max": 15, "default": 2},
        "handle_boxes": {"type": "bool", "default": True},
        "reduce_box_time": {"type": "bool", "default": True}
    },
    "Era Saga": {},
    "Breed Monsters": {
        "num_breeds": {"type": "int", "min": 1, "max": 100, "default": 20},
        "use_tree": {"type": "bool", "default": False},
        "feed_and_sell_monsters": {"type": "bool", "default": False},
        "sell": {"type": "bool", "default": False},
        "batch_size": {"type": "int", "min": 1, "max": 200, "default": 15, "hidden": True}
    },
    "Feed and Sell Monsters": {},
    "Craft Runes": {
        "num_runes": {"type": "int", "min": 1, "max": 100, "default": 10},
        "level": {"type": "choice", "choices": ["I", "II", "III", "IV", "V"], "default": "I"},
        "rune_type": {"type": "choice", "choices": ["Life", "Strength", "Stamina", "Speed", "Gold"], "default": "Life"},
        "team": {"type": "bool", "default": False}
    },
    "Close Game": {
        "action": {
            "type": "choice",
            "choices": ["Close Game Only", "Close Game & Exit Program", "Close Game & Shutdown Computer"],
            "default": "Close Game Only"
        }
    }
}

# =============================================================================
# GUI Command Descriptions
# =============================================================================

GUI_COMMAND_DESCRIPTIONS = {
    "PVP": {
        "title": "PVP Battles",
        "description": "Automatically fight PVP battles.\n\n"
                       "Features:\n"
                       "• Auto battle multiple times\n"
                       "• Handle rewards\n"
                       "• Option to reduce box open time if possible",
        "parameters": {
            "num_battles": "Number of PVP battles to fight",
            "handle_boxes": "Automatically open boxes when available and start unlocking new ones",
            "reduce_box_time": "Automatically watch ads to reduce box opening time (only works if handle_boxes is enabled)"
        }
    },
    "Era Saga": {
        "title": "Era Saga",
        "description": "Semi-automatic Era Saga. The user navigates to an Era Saga to run, then the app completes it.",
        "parameters": {}
    },
    "Resource Dungeons": {
        "title": "Resource Dungeons",
        "description": "Automatically complete all resource dungeons.\n\n"
                       "Goes through Maze Coin, Gem, and Rune dungeons in order and finishes them.",
        "parameters": {
            "wait_for_stamina": "Wait for stamina to refill when empty. The program will pause for 10 minutes to wait for stamina to refill"
        }
    },
    "Ads": {
        "title": "Watch Ads",
        "description": "Semi-automatic. Navigate to Monster Wood first, then the app plays all available ads, spins the wheel, and collects rewards.",
        "parameters": {}
    },
    "Reduce Time": {
        "title": "Reduce Time",
        "description": "Automatically watch a set number of ads to reduce cooldown timers.\n\n"
                       "Features:\n"
                       "• User sets how many ads to watch\n"
                       "• Auto-skips ads and waits out timers",
        "parameters": {
            "number_of_ads": "Maximum number of ads to watch (stops after reaching this count)"
        },
    },
    "Cavern": {
        "title": "Cavern Dungeons",
        "description": "Automatically complete selected cavern dungeons.\n\n"
                       "Features:\n"
                       "• Select Ancestral and/or Era dungeons via tabs\n"
                       "• Ancestral dungeons complete in one run\n"
                       "• Era dungeons repeat sub-dungeons up to your limit\n"
                       "• Team switching uses monsters named '1', '2', '3'",
        "parameters": {
            "caverns": "Select which cavern dungeons to complete (organized by tab)",
            "max_rooms": "Maximum sub-dungeons per Era dungeon (0 = unlimited)",
            "change_team": "Enable team switching to use monsters named '1', '2', '3'"
        }
    },
    "Breed Monsters": {
        "title": "Breed Monsters",
        "description": "Automatically breed monsters and manage the hatchery.\n\n"
                       "Features:\n"
                       "• Breed multiple times using the repeat button\n"
                       "• Choose between Mountain or Tree breeding locations\n"
                       "• Automatically hatches eggs and places/sells monsters\n"
                       "• Optional automatic feeding and selling in batches",
        "parameters": {
            "num_breeds": "Total number of breeds to perform",
            "use_tree": "Use Tree instead of Mountain for breeding",
            "feed_and_sell_monsters": "Feed and sell monsters after each batch",
            "sell": "Sell hatched monsters instead of placing them in vault",
            "batch_size": "Number of breeds between each feed/sell cycle"
        }
    },
    "Feed and Sell Monsters": {
        "title": "Feed and Sell Monsters",
        "description": "Semi-automatic. Open the vault, then the app feeds and sells Pandakenes and Greenasaurs",
        "parameters": {}
    },
    "Craft Runes": {
        "title": "Craft Runes",
        "description": "Semi-automatic. Navigate to the rune crafting screen first, then the app crafts the selected runes.",
        "parameters": {
            "num_runes": "Number of runes to craft",
            "level": "Rune level (I, II, III, IV, V)",
            "rune_type": "Type of rune to craft (Life, Strength, Stamina, Speed, Gold)",
            "team": "Craft a team rune instead of a standard one"
        }
    },
    "Close Game": {
        "title": "Close Game",
        "description": "Closes the game, locks the device, and optionally exits or shuts down.\n\n"
                       "• Closes Monster Legends gracefully\n"
                       "• Locks the Android device after closing\n"
                       "• Optional: exit program or shutdown PC",
        "parameters": {
            "action": "Close Game Only: just closes the game\n"
                       "Close Game & Exit Program: closes game and exits AutoMonster\n"
                       "Close Game & Shutdown Computer: closes game, exits, and shuts down PC (10s warning)"
        }
    }
}
