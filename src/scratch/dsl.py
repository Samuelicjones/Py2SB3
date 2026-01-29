"""
Scratch DSL - Domain Specific Language stubs for Scratch blocks.

Import this module to get IDE autocompletion and type checking for Scratch code:

    from scratch.dsl import *

    class Cat:
        def when_flag_clicked(self):
            say("Hello!")
            move(10)

These functions are stubs - they document the Scratch API but don't execute.
The actual execution happens when transpiled to .sb3 and run in Scratch.
"""

from typing import Union, Any, List, Optional

# Type aliases for Scratch values
Number = Union[int, float]
ScratchValue = Union[str, int, float, bool]


# ============================================================================
# Motion Blocks
# ============================================================================

def move(steps: Number) -> None:
    """Move the sprite forward by the specified number of steps."""
    pass

def turn_right(degrees: Number) -> None:
    """Turn the sprite clockwise by the specified degrees."""
    pass

def turn_left(degrees: Number) -> None:
    """Turn the sprite counter-clockwise by the specified degrees."""
    pass

def go_to(target: str) -> None:
    """Go to a target: "random", "mouse", or sprite name."""
    pass

def go_to_xy(x: Number, y: Number) -> None:
    """Go to the specified x, y coordinates."""
    pass

def glide_to(secs: Number, target: str) -> None:
    """Glide to a target over the specified seconds."""
    pass

def glide_to_xy(secs: Number, x: Number, y: Number) -> None:
    """Glide to x, y coordinates over the specified seconds."""
    pass

def point_in_direction(direction: Number) -> None:
    """Point the sprite in the specified direction (0=up, 90=right)."""
    pass

def point_towards(target: str) -> None:
    """Point towards a target: "mouse" or sprite name."""
    pass

def change_x(dx: Number) -> None:
    """Change the sprite's x position by dx."""
    pass

def set_x(x: Number) -> None:
    """Set the sprite's x position."""
    pass

def change_y(dy: Number) -> None:
    """Change the sprite's y position by dy."""
    pass

def set_y(y: Number) -> None:
    """Set the sprite's y position."""
    pass

def if_on_edge_bounce() -> None:
    """If the sprite is touching the edge, bounce."""
    pass

def set_rotation_style(style: str) -> None:
    """Set rotation style: "left-right", "don't rotate", or "all around"."""
    pass

def x_position() -> Number:
    """Get the sprite's x position."""
    return 0

def y_position() -> Number:
    """Get the sprite's y position."""
    return 0

def direction() -> Number:
    """Get the sprite's direction."""
    return 90


# ============================================================================
# Looks Blocks
# ============================================================================

def say(message: ScratchValue) -> None:
    """Display a speech bubble with the message."""
    pass

def say_for_secs(message: ScratchValue, secs: Number) -> None:
    """Display a speech bubble for the specified seconds."""
    pass

def think(message: ScratchValue) -> None:
    """Display a thought bubble with the message."""
    pass

def think_for_secs(message: ScratchValue, secs: Number) -> None:
    """Display a thought bubble for the specified seconds."""
    pass

def switch_costume(costume: str) -> None:
    """Switch to the specified costume by name or number."""
    pass

def next_costume() -> None:
    """Switch to the next costume."""
    pass

def switch_backdrop(backdrop: str) -> None:
    """Switch to the specified backdrop."""
    pass

def next_backdrop() -> None:
    """Switch to the next backdrop."""
    pass

def change_size(amount: Number) -> None:
    """Change the sprite's size by the specified amount."""
    pass

def set_size(size: Number) -> None:
    """Set the sprite's size to the specified percentage."""
    pass

def change_effect(effect: str, amount: Number) -> None:
    """Change a graphic effect by the specified amount.
    
    Effects: "color", "fisheye", "whirl", "pixelate", "mosaic", "brightness", "ghost"
    """
    pass

def set_effect(effect: str, value: Number) -> None:
    """Set a graphic effect to the specified value."""
    pass

def clear_effects() -> None:
    """Clear all graphic effects."""
    pass

def show() -> None:
    """Show the sprite."""
    pass

def hide() -> None:
    """Hide the sprite."""
    pass

def go_to_layer(layer: str) -> None:
    """Go to front or back layer: "front" or "back"."""
    pass

def change_layer(direction: str, layers: Number) -> None:
    """Change layer by number: direction is "forward" or "backward"."""
    pass

def costume_number() -> Number:
    """Get the current costume number."""
    return 1

def costume_name() -> str:
    """Get the current costume name."""
    return ""

def backdrop_number() -> Number:
    """Get the current backdrop number."""
    return 1

def backdrop_name() -> str:
    """Get the current backdrop name."""
    return ""

def size() -> Number:
    """Get the sprite's size."""
    return 100


# ============================================================================
# Sound Blocks
# ============================================================================

def play_sound(sound: str) -> None:
    """Start playing a sound."""
    pass

def play_sound_until_done(sound: str) -> None:
    """Play a sound and wait until it finishes."""
    pass

def stop_all_sounds() -> None:
    """Stop all sounds."""
    pass

def change_volume(amount: Number) -> None:
    """Change the volume by the specified amount."""
    pass

def set_volume(volume: Number) -> None:
    """Set the volume to the specified percentage (0-100)."""
    pass

def volume() -> Number:
    """Get the current volume."""
    return 100

def change_effect_sound(effect: str, amount: Number) -> None:
    """Change a sound effect (pitch, pan) by amount."""
    pass

def set_effect_sound(effect: str, value: Number) -> None:
    """Set a sound effect to a value."""
    pass

def clear_sound_effects() -> None:
    """Clear all sound effects."""
    pass


# ============================================================================
# Events Blocks (used as method decorators/names)
# ============================================================================

def broadcast(message: str) -> None:
    """Broadcast a message to all sprites."""
    pass

def broadcast_and_wait(message: str) -> None:
    """Broadcast a message and wait for all handlers to complete."""
    pass


# ============================================================================
# Control Blocks
# ============================================================================

def wait(secs: Number) -> None:
    """Wait for the specified number of seconds."""
    pass

def wait_until(condition: bool) -> None:
    """Wait until the condition is true."""
    pass

def stop(what: str = "all") -> None:
    """Stop scripts: "all", "this script", or "other scripts in sprite"."""
    pass

def create_clone(target: str = "myself") -> None:
    """Create a clone of the target sprite."""
    pass

def delete_this_clone() -> None:
    """Delete this clone."""
    pass


# ============================================================================
# Sensing Blocks
# ============================================================================

def touching(target: str) -> bool:
    """Check if touching a target: "mouse", "edge", or sprite name."""
    return False

def touching_color(color: str) -> bool:
    """Check if touching a color (hex string like "#FF0000")."""
    return False

def color_touching_color(color1: str, color2: str) -> bool:
    """Check if color1 on sprite is touching color2."""
    return False

def distance_to(target: str) -> Number:
    """Get distance to a target: "mouse" or sprite name."""
    return 0

def ask(question: str) -> None:
    """Ask a question and wait for user input."""
    pass

def answer() -> str:
    """Get the user's answer from the last ask block."""
    return ""

def key_pressed(key: str) -> bool:
    """Check if a key is pressed."""
    return False

def mouse_down() -> bool:
    """Check if the mouse button is pressed."""
    return False

def mouse_x() -> Number:
    """Get the mouse x position."""
    return 0

def mouse_y() -> Number:
    """Get the mouse y position."""
    return 0

def set_drag_mode(mode: str) -> None:
    """Set drag mode: "draggable" or "not draggable"."""
    pass

def loudness() -> Number:
    """Get the microphone loudness (0-100)."""
    return 0

def timer() -> Number:
    """Get the timer value in seconds."""
    return 0

def reset_timer() -> None:
    """Reset the timer to 0."""
    pass

def property_of(property: str, target: str) -> ScratchValue:
    """Get a property of another sprite or the stage.
    
    Properties: "x position", "y position", "direction", "costume #", 
                "costume name", "backdrop #", "backdrop name", "size", "volume"
    """
    return 0

def current(unit: str) -> Number:
    """Get current date/time: "year", "month", "date", "dayofweek", "hour", "minute", "second"."""
    return 0

def days_since_2000() -> Number:
    """Get the number of days since January 1, 2000."""
    return 0

def username() -> str:
    """Get the username of the current Scratch user."""
    return ""


# ============================================================================
# Operators
# ============================================================================

def pick_random(from_val: Number, to_val: Number) -> Number:
    """Pick a random number between from_val and to_val (inclusive)."""
    return 0

def join(str1: ScratchValue, str2: ScratchValue) -> str:
    """Join two strings together."""
    return str(str1) + str(str2)

def letter_of(index: Number, string: str) -> str:
    """Get the letter at the specified index (1-based)."""
    return ""

def length_of(string: str) -> Number:
    """Get the length of a string."""
    return len(string) if isinstance(string, str) else 0

def contains(string: str, substring: str) -> bool:
    """Check if string contains substring."""
    return False

def mod(a: Number, b: Number) -> Number:
    """Get the remainder of a divided by b."""
    return 0

def round_num(n: Number) -> Number:
    """Round a number to the nearest integer."""
    return round(n)

def math_op(op: str, n: Number) -> Number:
    """Perform a math operation: "abs", "floor", "ceiling", "sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "ln", "log", "e ^", "10 ^"."""
    return 0


# ============================================================================
# Variables (these are created dynamically)
# ============================================================================

def set_variable(name: str, value: ScratchValue) -> None:
    """Set a variable to a value. (Use assignment instead: var = value)"""
    pass

def change_variable(name: str, amount: Number) -> None:
    """Change a variable by an amount. (Use += instead: var += amount)"""
    pass

def show_variable(name: str) -> None:
    """Show a variable monitor on the stage."""
    pass

def hide_variable(name: str) -> None:
    """Hide a variable monitor."""
    pass


# ============================================================================
# Lists
# ============================================================================

def add_to_list(item: ScratchValue, list_name: str) -> None:
    """Add an item to the end of a list."""
    pass

def delete_of_list(index: Union[Number, str], list_name: str) -> None:
    """Delete item at index from list. Index can be number, "last", or "all"."""
    pass

def delete_all_of_list(list_name: str) -> None:
    """Delete all items from a list."""
    pass

def insert_at_list(item: ScratchValue, index: Number, list_name: str) -> None:
    """Insert item at the specified index in a list."""
    pass

def replace_item_of_list(index: Number, list_name: str, value: ScratchValue) -> None:
    """Replace item at index in list with a new value."""
    pass

def item_of_list(index: Number, list_name: str) -> ScratchValue:
    """Get the item at the specified index in a list."""
    return ""

def index_in_list(item: ScratchValue, list_name: str) -> Number:
    """Get the index of an item in a list (0 if not found)."""
    return 0

def length_of_list(list_name: str) -> Number:
    """Get the number of items in a list."""
    return 0

def list_contains(list_name: str, item: ScratchValue) -> bool:
    """Check if a list contains an item."""
    return False

def show_list(list_name: str) -> None:
    """Show a list monitor on the stage."""
    pass

def hide_list(list_name: str) -> None:
    """Hide a list monitor."""
    pass


# ============================================================================
# Pen Extension
# ============================================================================

def erase_all() -> None:
    """Erase all pen marks on the stage."""
    pass

def stamp() -> None:
    """Stamp the sprite's image on the stage."""
    pass

def pen_down() -> None:
    """Put the pen down (start drawing)."""
    pass

def pen_up() -> None:
    """Lift the pen up (stop drawing)."""
    pass

def set_pen_color(color: str) -> None:
    """Set the pen color (hex string like "#FF0000")."""
    pass

def change_pen_param(param: str, amount: Number) -> None:
    """Change a pen parameter by amount: "color", "saturation", "brightness", "transparency"."""
    pass

def set_pen_param(param: str, value: Number) -> None:
    """Set a pen parameter: "color", "saturation", "brightness", "transparency"."""
    pass

def change_pen_size(amount: Number) -> None:
    """Change the pen size by the specified amount."""
    pass

def set_pen_size(size: Number) -> None:
    """Set the pen size."""
    pass


# ============================================================================
# Music Extension
# ============================================================================

def play_drum(drum: Number, beats: Number) -> None:
    """Play a drum sound for the specified beats."""
    pass

def rest(beats: Number) -> None:
    """Rest (pause) for the specified beats."""
    pass

def play_note(note: Number, beats: Number) -> None:
    """Play a note for the specified beats."""
    pass

def set_instrument(instrument: Number) -> None:
    """Set the instrument (1-21)."""
    pass

def set_tempo(tempo: Number) -> None:
    """Set the tempo in beats per minute."""
    pass

def change_tempo(amount: Number) -> None:
    """Change the tempo by the specified amount."""
    pass

def tempo() -> Number:
    """Get the current tempo."""
    return 60


# ============================================================================
# Export all functions
# ============================================================================
# Sprite and Backdrop Builders
# ============================================================================

class Costume:
    """
    Define a custom costume for a sprite.
    
    Example:
        costume = Costume("my_costume", "path/to/image.png")
        costume = Costume("my_costume", "path/to/image.svg")
        costume = Costume("my_costume", svg_string="<svg>...</svg>")
    """
    def __init__(
        self, 
        name: str, 
        file_path: str = None, 
        *, 
        svg_string: str = None,
        rotation_center_x: Number = None,
        rotation_center_y: Number = None
    ):
        self.name = name
        self.file_path = file_path
        self.svg_string = svg_string
        self.rotation_center_x = rotation_center_x
        self.rotation_center_y = rotation_center_y
        
        if file_path is None and svg_string is None:
            raise ValueError("Must provide either file_path or svg_string")


class Sound:
    """
    Define a custom sound for a sprite.
    
    Example:
        sound = Sound("my_sound", "path/to/sound.wav")
        sound = Sound("my_sound", "path/to/sound.mp3")
    """
    def __init__(
        self,
        name: str,
        file_path: str,
        *,
        rate: int = None,
        sample_count: int = None
    ):
        self.name = name
        self.file_path = file_path
        self.rate = rate
        self.sample_count = sample_count


class SpriteConfig:
    """
    Configuration for a custom sprite with custom costumes and sounds.
    
    Use as a class decorator or inherit from it to configure sprites.
    
    Example:
        @sprite(
            costumes=[
                Costume("costume1", "player1.png"),
                Costume("costume2", "player2.png"),
            ],
            sounds=[
                Sound("jump", "jump.wav"),
            ],
            x=0, y=0, size=100
        )
        class Player:
            def when_flag_clicked(self):
                say("Hello!")
    """
    def __init__(
        self,
        costumes: List['Costume'] = None,
        sounds: List['Sound'] = None,
        x: Number = 0,
        y: Number = 0,
        size: Number = 100,
        direction: Number = 90,
        rotation_style: str = "all around",
        visible: bool = True,
        draggable: bool = False
    ):
        self.costumes = costumes or []
        self.sounds = sounds or []
        self.x = x
        self.y = y
        self.size = size
        self.direction = direction
        self.rotation_style = rotation_style
        self.visible = visible
        self.draggable = draggable


def sprite(
    costumes: List[Costume] = None,
    sounds: List[Sound] = None,
    x: Number = 0,
    y: Number = 0,
    size: Number = 100,
    direction: Number = 90,
    rotation_style: str = "all around",
    visible: bool = True,
    draggable: bool = False
):
    """
    Decorator to configure a sprite class with custom costumes and sounds.
    
    Example:
        @sprite(
            costumes=[
                Costume("idle", "sprites/player_idle.png"),
                Costume("walk", "sprites/player_walk.png"),
            ],
            sounds=[
                Sound("jump", "sounds/jump.wav"),
            ],
            x=-100, y=0, size=50
        )
        class Player:
            def when_flag_clicked(self):
                while True:
                    if key_pressed("space"):
                        play_sound("jump")
                        change_y(50)
    """
    def decorator(cls):
        # Store configuration as class attribute for transpiler to read
        cls._sprite_config = SpriteConfig(
            costumes=costumes,
            sounds=sounds,
            x=x, y=y, size=size,
            direction=direction,
            rotation_style=rotation_style,
            visible=visible,
            draggable=draggable
        )
        return cls
    return decorator


class BackdropConfig:
    """
    Configuration for custom stage backdrops.
    
    Example:
        backdrops = BackdropConfig([
            Backdrop("forest", "backgrounds/forest.png"),
            Backdrop("cave", "backgrounds/cave.png"),
        ])
    """
    def __init__(self, backdrops: List['Backdrop'] = None):
        self.backdrops = backdrops or []


class Backdrop:
    """
    Define a custom backdrop for the stage.
    
    Example:
        backdrop = Backdrop("my_backdrop", "path/to/image.png")
        backdrop = Backdrop("my_backdrop", svg_string="<svg>...</svg>")
    """
    def __init__(
        self,
        name: str,
        file_path: str = None,
        *,
        svg_string: str = None
    ):
        self.name = name
        self.file_path = file_path
        self.svg_string = svg_string
        
        if file_path is None and svg_string is None:
            raise ValueError("Must provide either file_path or svg_string")


# Global stage configuration (set before classes)
_stage_config = None

def configure_stage(
    backdrops: List[Backdrop] = None,
    sounds: List[Sound] = None,
    tempo: int = 60,
    volume: int = 100
):
    """
    Configure the stage with custom backdrops and sounds.
    
    Call this at the top of your file, before defining sprite classes.
    
    Example:
        from scratch.dsl import *
        
        configure_stage(
            backdrops=[
                Backdrop("forest", "backgrounds/forest.png"),
                Backdrop("cave", "backgrounds/cave.svg"),
                Backdrop("sky", svg_string='<svg>...</svg>'),
            ],
            sounds=[
                Sound("background_music", "music/theme.mp3"),
            ]
        )
        
        class Player:
            def when_flag_clicked(self):
                switch_backdrop("forest")
    """
    global _stage_config
    _stage_config = {
        'backdrops': backdrops or [],
        'sounds': sounds or [],
        'tempo': tempo,
        'volume': volume
    }


def get_stage_config():
    """Get the current stage configuration (used by transpiler)."""
    return _stage_config


# ============================================================================

__all__ = [
    # Motion
    'move', 'turn_right', 'turn_left', 'go_to', 'go_to_xy', 'glide_to', 'glide_to_xy',
    'point_in_direction', 'point_towards', 'change_x', 'set_x', 'change_y', 'set_y',
    'if_on_edge_bounce', 'set_rotation_style', 'x_position', 'y_position', 'direction',
    
    # Looks
    'say', 'say_for_secs', 'think', 'think_for_secs', 'switch_costume', 'next_costume',
    'switch_backdrop', 'next_backdrop', 'change_size', 'set_size', 'change_effect',
    'set_effect', 'clear_effects', 'show', 'hide', 'go_to_layer', 'change_layer',
    'costume_number', 'costume_name', 'backdrop_number', 'backdrop_name', 'size',
    
    # Sound
    'play_sound', 'play_sound_until_done', 'stop_all_sounds', 'change_volume',
    'set_volume', 'volume', 'change_effect_sound', 'set_effect_sound', 'clear_sound_effects',
    
    # Events
    'broadcast', 'broadcast_and_wait',
    
    # Control
    'wait', 'wait_until', 'stop', 'create_clone', 'delete_this_clone',
    
    # Sensing
    'touching', 'touching_color', 'color_touching_color', 'distance_to', 'ask', 'answer',
    'key_pressed', 'mouse_down', 'mouse_x', 'mouse_y', 'set_drag_mode', 'loudness',
    'timer', 'reset_timer', 'property_of', 'current', 'days_since_2000', 'username',
    
    # Operators
    'pick_random', 'join', 'letter_of', 'length_of', 'contains', 'mod', 'round_num', 'math_op',
    
    # Variables
    'set_variable', 'change_variable', 'show_variable', 'hide_variable',
    
    # Lists
    'add_to_list', 'delete_of_list', 'delete_all_of_list', 'insert_at_list',
    'replace_item_of_list', 'item_of_list', 'index_in_list', 'length_of_list',
    'list_contains', 'show_list', 'hide_list',
    
    # Pen
    'erase_all', 'stamp', 'pen_down', 'pen_up', 'set_pen_color', 'change_pen_param',
    'set_pen_param', 'change_pen_size', 'set_pen_size',
    
    # Music
    'play_drum', 'rest', 'play_note', 'set_instrument', 'set_tempo', 'change_tempo', 'tempo',
    
    # Types
    'Number', 'ScratchValue',
    
    # Sprite/Backdrop configuration
    'Costume', 'Sound', 'Backdrop', 'SpriteConfig', 'BackdropConfig',
    'sprite', 'configure_stage', 'get_stage_config',
]
