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
            "choices": [
                "--Ancestral Caverns--",
                "evaris",
                "geneza",
                "jestin",
                "baba",
                "khalorc",
                "tyr",
                "robur",
                "theton",
                "griffania",
                "--Era Caverns--",
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
            ],
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
        "description": "Automatically do Era Saga.\n\n"
                       "Note: Make sure you are in the Era Saga you want to automate before running this command.",
        "parameters": {}
    },
    "Resource Dungeons": {
        "title": "Resource Dungeons",
        "description": "Automatically do all important dungeons.\n\n"
                       "Goes through Gem, Rune and Coin dungeons and finishes them.",
        "parameters": {
            "wait_for_stamina": "Wait for stamina to refill when empty. The program will pause for 10 minutes to wait for stamina to refill"
        }
    },
    "Ads": {
        "title": "Watch Ads",
        "description": "Automatically watch all available ads for rewards.\n\n"
                       "Note: Open MonsterWood before running this command.",
        "parameters": {}
    },
    "Reduce Time": {
        "title": "Reduce Time",
        "description": "Automatically watch as many selected ads as needed to reduce time.\n\n"
                       "Features:\n"
                       "• Select how many ads to watch to reduce time\n",
        "parameters": {
            "number_of_ads": "Number of ads to watch to reduce time"
        },
    },
    "Cavern": {
        "title": "Cavern Dungeons",
        "description": "Automatically do selected cavern dungeons.\n\n"
                       "Features:\n"
                       "• Select multiple dungeons to complete\n"
                       "• Control how many sub-dungeons to do\n"
                       "• Team management. Name '1', '2', '3' the monsters you want to use and the program will switch to them automatically",
        "parameters": {
            "ancestral": "Select which ancestral cavern dungeons to complete",
            "era": "Select which era cavern dungeons to complete",
            "max_rooms": "Maximum number of rooms to explore",
            "change_team": "Enable team switching to use selected monsters"
        }
    },
    "Breed Monsters": {
        "title": "Breed Monsters",
        "description": "Automatically breed monsters.\n\n"
                       "Features:\n"
                       "• Breed multiple times using the repeat button\n"
                       "• Choose between Mountain or Tree breeding locations\n"
                       "• Automatically handles the breeding sequence\n"
                       "• Optional automatic feeding and selling of monsters",
        "parameters": {
            "num_breeds": "Number of times to breed monsters",
            "use_tree": "Use Tree instead of Mountain for breeding",
            "feed_and_sell_monsters": "Automatically feed and sell monsters every 20 breeds",
            "sell": "Automatically sell monsters after hatching"
        }
    },
    "Feed and Sell Monsters": {
        "title": "Feed and Sell Monsters",
        "description": "Automatically feed and sell monsters.\n\n"
                       "Features:\n"
                       "• Process all monsters in sequence\n"
                       "• Feed monsters to level them up\n"
                       "• Sell unwanted monsters for resources",
        "parameters": {}
    },
    "Craft Runes": {
        "title": "Craft Runes",
        "description": "Craft runes for monsters.\n\n"
                       "Features:\n"
                       "• Select number of runes to craft\n"
                       "• Choose rune level (1-14)\n"
                       "• Option to craft for team monsters",
        "parameters": {
            "num_runes": "Number of runes to craft",
            "level": "Rune level (1-14)",
            "rune_type": "Type of rune to craft",
            "team": "Craft for team monsters"
        }
    },
    "Close Game": {
        "title": "Close Game",
        "description": "Closes the game gracefully.\n\n"
                       "Features:\n"
                       "• Close Game Only - Just closes the game\n"
                       "• Close Game & Exit Program - Closes game and exits AutoMonster\n"
                       "• Close Game & Shutdown Computer - Closes game, exits, and shuts down PC",
        "parameters": {
            "action": "Select what to do after closing the game"
        }
    }
}
