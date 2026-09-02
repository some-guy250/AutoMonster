"""Single source of truth for GUI commands.

Each command is one ``CommandSpec`` bundling:
  - ``params``: the parameter field definitions rendered by ``CommandFrame``
  - ``run``: an adapter ``run(controller, progress_callback, **params)`` that
    maps the GUI parameter names onto the controller method call
  - ``title`` / ``description`` / ``param_help``: the help popup content

This replaces the previous three parallel structures (``GUI_COMMANDS`` param
specs, ``GUI_COMMAND_DESCRIPTIONS`` help text, and the if/elif ladder in
``ControllerGUI.get_command_callback``).
"""

from dataclasses import dataclass, field
from typing import Callable, Dict

from config.config import CloseAction


@dataclass(frozen=True)
class CommandSpec:
    name: str
    params: Dict[str, dict]
    run: Callable
    title: str = ""
    description: str = ""
    param_help: Dict[str, str] = field(default_factory=dict)


# Commands that report fractional progress (0.0 .. 1.0) via the progress bar.
PROGRESS_COMMANDS = ("PVP", "Cavern", "Breed Monsters")


COMMANDS: Dict[str, CommandSpec] = {
    "Resource Dungeons": CommandSpec(
        name="Resource Dungeons",
        params={
            "wait_for_stamina": {"type": "bool", "default": False},
        },
        run=lambda c, prog, **p: c.do_resource_dungeons(
            wait_for_stamina_to_refill=p.get("wait_for_stamina", False)
        ),
        title="Resource Dungeons",
        description=(
            "Automatically complete all resource dungeons.\n\n"
            "Goes through Maze Coin, Gem, and Rune dungeons in order and finishes them."
        ),
        param_help={
            "wait_for_stamina": (
                "Wait for stamina to refill when empty. The program will pause for "
                "10 minutes to wait for stamina to refill"
            ),
        },
    ),
    "Ads": CommandSpec(
        name="Ads",
        params={},
        run=lambda c, prog, **p: c.play_ads(),
        title="Watch Ads",
        description=(
            "Semi-automatic. Navigate to Monster Wood first, then the app plays all "
            "available ads, spins the wheel, and collects rewards."
        ),
        param_help={},
    ),
    "Reduce Time": CommandSpec(
        name="Reduce Time",
        params={
            "number_of_ads": {"type": "int", "min": 1, "max": 4, "default": 4},
        },
        run=lambda c, prog, **p: c.reduce_time(p.get("number_of_ads", 3)),
        title="Reduce Time",
        description=(
            "Automatically watch a set number of ads to reduce cooldown timers.\n\n"
            "Features:\n"
            "• User sets how many ads to watch\n"
            "• Auto-skips ads and waits out timers"
        ),
        param_help={
            "number_of_ads": "Maximum number of ads to watch (stops after reaching this count)",
        },
    ),
    "Cavern": CommandSpec(
        name="Cavern",
        params={
            "caverns": {
                "type": "multiple_choice",
                "tabs": {
                    "Ancestral": [
                        "evaris", "geneza", "jestin", "baba", "khalorc",
                        "tyr", "robur", "theton", "griffania",
                    ],
                    "Era": [
                        "misery", "conspiracy", "feral", "historia", "multiverse",
                        "alpine", "abyssal", "galactic", "blossom", "doomed",
                        "metro", "corrupted", "cosmic", "original",
                    ],
                },
                "default": [],
            },
            "max_rooms": {"type": "int", "min": 1, "max": 5, "default": 3},
            "change_team": {"type": "bool", "default": True},
        },
        run=lambda c, prog, **p: c.do_cavern(
            *p.get("caverns", []),
            max_rooms=p.get("max_rooms", 3),
            change_team=p.get("change_team", True),
            progress_callback=prog,
        ),
        title="Cavern Dungeons",
        description=(
            "Automatically complete selected cavern dungeons.\n\n"
            "Features:\n"
            "• Select Ancestral and/or Era dungeons via tabs\n"
            "• Ancestral dungeons complete in one run\n"
            "• Era dungeons repeat sub-dungeons up to your limit\n"
            "• Team switching uses monsters named '1', '2', '3'"
        ),
        param_help={
            "caverns": "Select which cavern dungeons to complete (organized by tab)",
            "max_rooms": "Maximum sub-dungeons per Era dungeon (0 = unlimited)",
            "change_team": "Enable team switching to use monsters named '1', '2', '3'",
        },
    ),
    "Do Dungeon": CommandSpec(
        name="Do Dungeon",
        params={
            "has_wheel": {"type": "bool", "default": False},
            "has_cutscene": {"type": "bool", "default": False},
            "has_stamina": {"type": "bool", "default": False},
            "max_nodes": {"type": "int", "min": 0, "max": 20, "default": 0},
            "max_losses": {"type": "int", "min": 0, "max": 5, "default": 3},
            "wait_for_stamina_to_refill": {"type": "bool", "default": True},
        },
        run=lambda c, prog, **p: c.do_dungeon(
            p.get("has_wheel", False),
            p.get("has_cutscene", False),
            p.get("has_stamina", False),
            max_nodes=(p.get("max_nodes", 0) or None),
            max_losses=(p.get("max_losses", 3) or -1),
            wait_for_stamina_to_refill=p.get("wait_for_stamina_to_refill", True),
            change_team=False,
        ),
        title="Do Dungeon (Generic)",
        description=(
            "Semi-automatic. Navigate to the dungeon you want to run first, then the "
            "app clears it: fights each node, skips cutscenes, and spins the wheel where "
            "it appears.\n\n"
            "Use this for random / one-time dungeons."
        ),
        param_help={
            "has_wheel": "Dungeon has a spin wheel to collect after each battle",
            "has_cutscene": "Dungeon shows a cutscene to skip before the battle",
            "has_stamina": "Dungeon costs stamina (waits / stops when it runs out)",
            "max_nodes": "Number of nodes to fight (0 = run the whole dungeon)",
            "max_losses": "Stop after this many consecutive losses (0 = never stop)",
            "wait_for_stamina_to_refill": "When stamina empties, wait 10 minutes for it to refill instead of stopping",
        },
    ),
    "PVP": CommandSpec(
        name="PVP",
        params={
            "num_battles": {"type": "int", "min": 1, "max": 15, "default": 2},
            "handle_boxes": {"type": "bool", "default": True},
            "reduce_box_time": {"type": "bool", "default": True},
        },
        run=lambda c, prog, **p: c.do_pvp(
            p.get("num_battles", 2),
            p.get("handle_boxes", True),
            p.get("reduce_box_time", True),
            progress_callback=prog,
        ),
        title="PVP Battles",
        description=(
            "Automatically fight PVP battles.\n\n"
            "Features:\n"
            "• Auto battle multiple times\n"
            "• Handle rewards\n"
            "• Option to reduce box open time if possible"
        ),
        param_help={
            "num_battles": "Number of PVP battles to fight",
            "handle_boxes": "Automatically open boxes when available and start unlocking new ones",
            "reduce_box_time": "Automatically watch ads to reduce box opening time (only works if handle_boxes is enabled)",
        },
    ),
    "Era Saga": CommandSpec(
        name="Era Saga",
        params={},
        run=lambda c, prog, **p: c.do_era_saga(),
        title="Era Saga",
        description=(
            "Semi-automatic Era Saga. The user navigates to an Era Saga to run, "
            "then the app completes it."
        ),
        param_help={},
    ),
    "Breed Monsters": CommandSpec(
        name="Breed Monsters",
        params={
            "num_breeds": {"type": "int", "min": 1, "max": 100, "default": 20},
            "use_tree": {"type": "bool", "default": False},
            "feed_and_sell_monsters": {"type": "bool", "default": False},
            "sell": {"type": "bool", "default": False},
            "batch_size": {"type": "int", "min": 1, "max": 200, "default": 15, "hidden": True},
        },
        run=lambda c, prog, **p: c.breed_monsters(
            p.get("num_breeds", 1),
            p.get("use_tree", False),
            p.get("feed_and_sell_monsters", False),
            p.get("sell", False),
            batch_size=p.get("batch_size", 15),
            progress_callback=prog,
        ),
        title="Breed Monsters",
        description=(
            "Automatically breed monsters and manage the hatchery.\n\n"
            "Features:\n"
            "• Breed multiple times using the repeat button\n"
            "• Choose between Mountain or Tree breeding locations\n"
            "• Automatically hatches eggs and places/sells monsters\n"
            "• Optional automatic feeding and selling in batches"
        ),
        param_help={
            "num_breeds": "Total number of breeds to perform",
            "use_tree": "Use Tree instead of Mountain for breeding",
            "feed_and_sell_monsters": "Feed and sell monsters after each batch",
            "sell": "Sell hatched monsters instead of placing them in vault",
            "batch_size": "Number of breeds between each feed/sell cycle",
        },
    ),
    "Feed and Sell Monsters": CommandSpec(
        name="Feed and Sell Monsters",
        params={},
        run=lambda c, prog, **p: c.feed_and_sell_monsters(),
        title="Feed and Sell Monsters",
        description=(
            "Semi-automatic. Open the vault, then the app feeds and sells "
            "Pandakenes and Greenasaurs"
        ),
        param_help={},
    ),
    "Craft Runes": CommandSpec(
        name="Craft Runes",
        params={
            "num_runes": {"type": "int", "min": 1, "max": 100, "default": 10},
            "level": {"type": "choice", "choices": ["I", "II", "III", "IV", "V"], "default": "I"},
            "rune_type": {"type": "choice", "choices": ["Life", "Strength", "Stamina", "Speed", "Gold"], "default": "Life"},
            "team": {"type": "bool", "default": False},
        },
        run=lambda c, prog, **p: c.craft_runes(
            p.get("num_runes", 10),
            p.get("level", "I"),
            p.get("rune_type", "Life"),
            p.get("team", False),
            progress_callback=prog,
        ),
        title="Craft Runes",
        description=(
            "Semi-automatic. Navigate to the rune crafting screen first, then the app "
            "crafts the selected runes."
        ),
        param_help={
            "num_runes": "Number of runes to craft",
            "level": "Rune level (I, II, III, IV, V)",
            "rune_type": "Type of rune to craft (Life, Strength, Stamina, Speed, Gold)",
            "team": "Craft a team rune instead of a standard one",
        },
    ),
    "Close Game": CommandSpec(
        name="Close Game",
        params={
            "action": {
                "type": "choice",
                "choices": [a.value for a in CloseAction],
                "default": CloseAction.GAME_ONLY.value,
            },
        },
        run=lambda c, prog, **p: c.close_game(
            action=CloseAction.from_display(p.get("action", CloseAction.GAME_ONLY.value))
        ),
        title="Close Game",
        description=(
            "Closes the game, locks the device, and optionally exits or shuts down.\n\n"
            "• Closes Monster Legends gracefully\n"
            "• Locks the Android device after closing\n"
            "• Optional: exit program or shutdown PC"
        ),
        param_help={
            "action": (
                "Close Game Only: just closes the game\n"
                "Close Game & Exit Program: closes game and exits AutoMonster\n"
                "Close Game & Shutdown Computer: closes game, exits, and shuts down PC (10s warning)"
            ),
        },
    ),
}


def get_spec(name: str) -> CommandSpec:
    """Return the spec for a command name, raising for unknown commands."""
    spec = COMMANDS.get(name)
    if spec is None:
        raise ValueError(f"Unknown command: {name}")
    return spec
