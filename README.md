# Py2SB3

[![PyPI version](https://badge.fury.io/py/py2sb3.svg)](https://badge.fury.io/py/py2sb3)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A bidirectional Python to Scratch 3.0 transpiler. Write Scratch projects in Python, or convert existing Scratch projects to Python code.

## Features

- **Python → Scratch**: Write Python code and compile to `.sb3` files
- **Scratch → Python**: Convert existing `.sb3` projects to readable Python
- **Round-trip**: Convert Scratch → Python → Scratch while preserving all sprites and sounds
- **IDE Support**: Full autocomplete and type hints for all Scratch blocks
- **339 Official Sprites**: Access to the complete Scratch sprite library
- **Sound Library**: All official Scratch sounds available

## Installation

```bash
pip install py2sb3
```

Or install from source:

```bash
git clone https://github.com/Samuelicjones/Py2SB3.git
cd Py2SB3
pip install -e .
```

## Quick Start

### Writing Scratch in Python

```python
from scratch import transpile_to_json, save_sb3
from scratch.dsl import *  # IDE autocomplete for all blocks

class Cat:
    def when_flag_clicked(self):
        say("Hello!")
        for i in range(10):
            move(10)
            turn_right(15)
            wait(0.1)

    def when_key_space(self):
        play_sound("Meow")

# Compile to .sb3
code = open("my_game.py").read()
json_str = transpile_to_json(code)
save_sb3(json_str, "my_game.sb3")
```

### Converting Scratch to Python

```python
from scratch import convert_sb3_to_py

# Convert any .sb3 file to Python
convert_sb3_to_py("existing_project.sb3", "output.py")
```

### Round-trip Conversion

```python
from scratch import roundtrip_sb3

# Convert .sb3 → Python → .sb3 (preserves all sprites/sounds)
roundtrip_sb3("input.sb3", "output.sb3", py_path="intermediate.py")
```

## CLI Commands

```bash
# Python to Scratch
scratch py2sb3 game.py game.sb3

# Scratch to Python
scratch sb32py project.sb3 project.py

# Round-trip (preserves assets)
scratch roundtrip input.sb3 output.sb3 --py intermediate.py

# Show project info
scratch info project.sb3
```

## Sprite Classes

Each Python class becomes a Scratch sprite. The class name determines the sprite:

```python
class Cat:        # Uses official Cat sprite
    pass

class Dog1:       # Uses Dog1 sprite
    pass

class MySprite:   # Uses default sprite
    pass
```

## Event Handlers

Methods starting with `when_` become Scratch event handlers:

| Python Method | Scratch Block |
|--------------|---------------|
| `when_flag_clicked()` | Green flag clicked |
| `when_key_space()` | When space key pressed |
| `when_key_up()` | When up arrow pressed |
| `when_key_a()` | When 'a' key pressed |
| `when_clicked()` | When this sprite clicked |
| `when_broadcast_message1()` | When I receive "message1" |
| `when_i_start_as_clone()` | When I start as a clone |

## Supported Blocks

### Motion
```python
move(10)                    # Move 10 steps
turn_right(15)              # Turn right 15 degrees
turn_left(15)               # Turn left 15 degrees
go_to("random")             # Go to random position
go_to("mouse")              # Go to mouse pointer
go_to_xy(0, 0)              # Go to x, y
glide_to_xy(1, 100, 100)    # Glide to x, y in 1 second
point_in_direction(90)      # Point in direction
point_towards("mouse")      # Point towards mouse
change_x(10)                # Change x by 10
set_x(0)                    # Set x to 0
change_y(10)                # Change y by 10
set_y(0)                    # Set y to 0
if_on_edge_bounce()         # If on edge, bounce
set_rotation_style("left-right")
x_position()                # Reporter: x position
y_position()                # Reporter: y position
direction()                 # Reporter: direction
```

### Looks
```python
say("Hello!")               # Say
say_for_secs("Hi!", 2)      # Say for 2 seconds
think("Hmm...")             # Think
think_for_secs("...", 2)    # Think for 2 seconds
switch_costume("costume2")  # Switch costume
next_costume()              # Next costume
switch_backdrop("backdrop2")
next_backdrop()
change_size(10)             # Change size by 10
set_size(100)               # Set size to 100%
change_effect("color", 25)  # Change color effect
set_effect("ghost", 50)     # Set ghost effect
clear_effects()             # Clear graphic effects
show()                      # Show sprite
hide()                      # Hide sprite
go_to_layer("front")        # Go to front layer
change_layer("forward", 1)  # Go forward 1 layer
costume_number()            # Reporter
backdrop_name()             # Reporter
size()                      # Reporter
```

### Sound
```python
play_sound("Meow")          # Start sound
play_sound_until_done("Pop")# Play until done
stop_all_sounds()           # Stop all sounds
change_volume(-10)          # Change volume
set_volume(100)             # Set volume
volume()                    # Reporter
```

### Control
```python
wait(1)                     # Wait 1 second
for i in range(10):         # Repeat 10 times
    move(10)
while True:                 # Forever loop
    move(1)
if touching("edge"):        # If-then
    turn_right(180)
if x_position() > 0:        # If-else
    move(10)
else:
    move(-10)
wait_until(touching("edge"))# Wait until
while not touching("edge"): # Repeat until
    move(1)
stop("all")                 # Stop all/this script
create_clone("myself")      # Create clone
delete_this_clone()         # Delete this clone
```

### Sensing
```python
touching("mouse")           # Touching mouse pointer?
touching("edge")            # Touching edge?
touching("Sprite1")         # Touching sprite?
touching_color("#FF0000")   # Touching color?
color_touching_color("#FF0000", "#00FF00")
distance_to("mouse")        # Distance to
ask("What's your name?")    # Ask and wait
answer()                    # Answer reporter
key_pressed("space")        # Key pressed?
mouse_down()                # Mouse down?
mouse_x()                   # Mouse x
mouse_y()                   # Mouse y
timer()                     # Timer
reset_timer()               # Reset timer
property_of("x position", "Sprite1")
current("year")             # Current year/month/etc
days_since_2000()           # Days since 2000
username()                  # Username
```

### Operators
```python
pick_random(1, 10)          # Random number
join("hello", "world")      # Join strings
letter_of(1, "hello")       # Letter 1 of "hello"
length_of("hello")          # Length of string
contains("hello", "ell")    # Contains substring?
x % y                       # Modulo (use mod())
round_num(3.7)              # Round
math_op("abs", -5)          # abs/floor/ceiling/sqrt/sin/cos/tan/etc
```

### Variables
```python
my_var = 0                  # Create variable
my_var = 10                 # Set variable
my_var += 5                 # Change variable
show_variable("my_var")     # Show variable
hide_variable("my_var")     # Hide variable
```

### Lists
```python
my_list = []                # Create list
add_to_list("apple", "my_list")
delete_of_list(1, "my_list")
delete_all_of_list("my_list")
insert_at_list("banana", 1, "my_list")
replace_item_of_list(1, "my_list", "cherry")
item_of_list(1, "my_list")  # Reporter
index_in_list("apple", "my_list")
length_of_list("my_list")
list_contains("my_list", "apple")
```

### Custom Blocks
```python
def define_jump(self, height):
    """Custom block with argument"""
    change_y(height)
    wait(0.5)
    change_y(-height)

def when_flag_clicked(self):
    self.jump(50)  # Call custom block
```

## Using Official Sprites

The transpiler includes all 339 official Scratch sprites:

```python
from scratch import list_sprites, get_sprite_data

# List all available sprites
print(list_sprites())  # ['Abby', 'Amon', 'Andie', ...]

# Get sprite info
sprite = get_sprite_data("Cat")
print(f"Costumes: {len(sprite['costumes'])}")
print(f"Sounds: {len(sprite['sounds'])}")
```

## Using Sounds

```python
from scratch import list_sounds, get_library_sound_for_project

# List all sounds
print(list_sounds())  # ['A Bass', 'A Elec Bass', ...]

# Sounds are auto-detected from play_sound() calls
class Cat:
    def when_flag_clicked(self):
        play_sound("Meow")  # Auto-included in project
```

## Project Structure

```
Py2SB3/
├── src/scratch/
│   ├── __init__.py      # Package exports
│   ├── transpiler.py    # Core transpiler (Python ↔ Scratch)
│   ├── dsl.py           # IDE stubs for autocomplete
│   ├── library.py       # Sprite/sound library access
│   ├── cli.py           # Command-line interface
│   └── data/
│       ├── sprites_library.json
│       └── sounds_library.json
├── tests/
│   └── test_transpiler.py
├── pyproject.toml
└── README.md
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.