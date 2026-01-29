"""
Command-line interface for the Scratch Transpiler.

Usage:
    scratch py2sb3 input.py output.sb3     # Python to Scratch
    scratch sb32py input.sb3 output.py     # Scratch to Python  
    scratch roundtrip input.sb3 output.sb3 # Round-trip conversion
    scratch blocks                          # Show all available blocks
    scratch blocks motion                   # Show blocks for a category
"""

import argparse
import sys
from pathlib import Path


# Block reference organized by category
BLOCK_REFERENCE = {
    'motion': {
        'description': 'Movement and position blocks',
        'blocks': [
            ('move(steps)', 'Move forward by steps'),
            ('turn_right(degrees)', 'Turn clockwise'),
            ('turn_left(degrees)', 'Turn counter-clockwise'),
            ('go_to(target)', 'Go to target ("mouse", "random", or sprite name)'),
            ('go_to_xy(x, y)', 'Go to x, y position'),
            ('glide_to(secs, target)', 'Glide to target over time'),
            ('glide_to_xy(secs, x, y)', 'Glide to x, y over time'),
            ('point_in_direction(degrees)', 'Point in direction (0=up, 90=right)'),
            ('point_towards(target)', 'Point towards target'),
            ('change_x(dx)', 'Change x position by amount'),
            ('set_x(x)', 'Set x position'),
            ('change_y(dy)', 'Change y position by amount'),
            ('set_y(y)', 'Set y position'),
            ('if_on_edge_bounce()', 'Bounce if touching edge'),
            ('set_rotation_style(style)', 'Set rotation style ("left-right", "don\'t rotate", "all around")'),
            ('x_position()', 'Get x position (reporter)'),
            ('y_position()', 'Get y position (reporter)'),
            ('direction()', 'Get direction (reporter)'),
        ]
    },
    'looks': {
        'description': 'Appearance and visual effect blocks',
        'blocks': [
            ('say(message)', 'Say message in speech bubble'),
            ('say_for_secs(message, secs)', 'Say message for duration'),
            ('think(message)', 'Think message in thought bubble'),
            ('think_for_secs(message, secs)', 'Think message for duration'),
            ('switch_costume(name)', 'Switch to costume by name'),
            ('next_costume()', 'Switch to next costume'),
            ('switch_backdrop(name)', 'Switch backdrop by name'),
            ('next_backdrop()', 'Switch to next backdrop'),
            ('change_size(amount)', 'Change size by amount'),
            ('set_size(percent)', 'Set size to percent'),
            ('change_effect(effect, value)', 'Change effect (COLOR, GHOST, etc.)'),
            ('set_effect(effect, value)', 'Set effect to value'),
            ('clear_effects()', 'Clear all graphic effects'),
            ('show()', 'Show sprite'),
            ('hide()', 'Hide sprite'),
            ('go_to_layer(layer)', 'Go to front/back layer'),
            ('change_layer(direction, num)', 'Go forward/backward layers'),
            ('costume_number()', 'Get costume number (reporter)'),
            ('costume_name()', 'Get costume name (reporter)'),
            ('backdrop_number()', 'Get backdrop number (reporter)'),
            ('backdrop_name()', 'Get backdrop name (reporter)'),
            ('size()', 'Get size (reporter)'),
        ]
    },
    'sound': {
        'description': 'Sound and music blocks',
        'blocks': [
            ('play_sound(name)', 'Start playing sound'),
            ('play_sound_until_done(name)', 'Play sound and wait'),
            ('stop_all_sounds()', 'Stop all sounds'),
            ('change_sound_effect(effect, value)', 'Change sound effect (PITCH, PAN)'),
            ('set_sound_effect(effect, value)', 'Set sound effect'),
            ('clear_sound_effects()', 'Clear all sound effects'),
            ('change_volume(amount)', 'Change volume by amount'),
            ('set_volume(percent)', 'Set volume to percent'),
            ('volume()', 'Get volume (reporter)'),
        ]
    },
    'events': {
        'description': 'Event hat blocks (method names in sprite class)',
        'blocks': [
            ('def when_flag_clicked(self):', 'When green flag clicked'),
            ('def when_key_space(self):', 'When space key pressed'),
            ('def when_key_up(self):', 'When up arrow pressed'),
            ('def when_key_<key>(self):', 'When any key pressed (a-z, 0-9, etc.)'),
            ('def when_clicked(self):', 'When this sprite clicked'),
            ('def when_backdrop_<name>(self):', 'When backdrop switches to name'),
            ('def when_broadcast_<msg>(self):', 'When I receive broadcast'),
            ('def when_loudness_greater_than(self, threshold):', 'When loudness > threshold'),
            ('def when_timer_greater_than(self, threshold):', 'When timer > threshold'),
            ('broadcast(message)', 'Broadcast message'),
            ('broadcast_and_wait(message)', 'Broadcast and wait'),
        ]
    },
    'control': {
        'description': 'Control flow blocks',
        'blocks': [
            ('wait(secs)', 'Wait seconds'),
            ('for i in range(n):', 'Repeat n times'),
            ('while True:', 'Forever loop'),
            ('while condition:', 'Repeat until (negated condition)'),
            ('if condition:', 'If then'),
            ('if condition: ... else:', 'If then else'),
            ('stop("all")', 'Stop all/this script/other scripts'),
            ('create_clone("myself")', 'Create clone of myself or sprite'),
            ('delete_this_clone()', 'Delete this clone'),
            ('def when_i_start_as_clone(self):', 'When I start as a clone'),
        ]
    },
    'sensing': {
        'description': 'Sensing and input blocks',
        'blocks': [
            ('touching(target)', 'Touching sprite/mouse/edge? (boolean)'),
            ('touching_color(color)', 'Touching color? (boolean)'),
            ('color_touching_color(c1, c2)', 'Color touching color? (boolean)'),
            ('key_pressed(key)', 'Key pressed? (boolean)'),
            ('mouse_down()', 'Mouse down? (boolean)'),
            ('distance_to(target)', 'Distance to target (reporter)'),
            ('ask(question)', 'Ask and wait for input'),
            ('answer()', 'Get answer (reporter)'),
            ('mouse_x()', 'Mouse x position (reporter)'),
            ('mouse_y()', 'Mouse y position (reporter)'),
            ('loudness()', 'Get loudness (reporter)'),
            ('timer()', 'Get timer value (reporter)'),
            ('reset_timer()', 'Reset timer'),
            ('current_year()', 'Current year (reporter)'),
            ('current_month()', 'Current month (reporter)'),
            ('current_date()', 'Current date (reporter)'),
            ('current_day()', 'Current day of week (reporter)'),
            ('current_hour()', 'Current hour (reporter)'),
            ('current_minute()', 'Current minute (reporter)'),
            ('current_second()', 'Current second (reporter)'),
            ('days_since_2000()', 'Days since 2000 (reporter)'),
            ('username()', 'Get username (reporter)'),
        ]
    },
    'operators': {
        'description': 'Math and logic operators (use Python syntax)',
        'blocks': [
            ('a + b', 'Addition'),
            ('a - b', 'Subtraction'),
            ('a * b', 'Multiplication'),
            ('a / b', 'Division'),
            ('a % b', 'Modulo (remainder)'),
            ('a > b', 'Greater than'),
            ('a < b', 'Less than'),
            ('a == b', 'Equals'),
            ('a and b', 'Logical AND'),
            ('a or b', 'Logical OR'),
            ('not a', 'Logical NOT'),
            ('random(min, max)', 'Pick random number'),
            ('join(s1, s2)', 'Join strings'),
            ('letter_of(index, string)', 'Letter at index'),
            ('length(string)', 'Length of string'),
            ('contains(string, substring)', 'String contains?'),
            ('round(n)', 'Round number'),
            ('abs(n)', 'Absolute value'),
            ('floor(n)', 'Floor'),
            ('ceil(n)', 'Ceiling'),
            ('sqrt(n)', 'Square root'),
            ('sin(n)', 'Sine'),
            ('cos(n)', 'Cosine'),
            ('tan(n)', 'Tangent'),
        ]
    },
    'variables': {
        'description': 'Variable blocks (use Python syntax)',
        'blocks': [
            ('x = value', 'Set variable to value'),
            ('x += value', 'Change variable by value'),
            ('x', 'Read variable (in expressions)'),
            ('show_variable(name)', 'Show variable on stage'),
            ('hide_variable(name)', 'Hide variable from stage'),
        ]
    },
    'lists': {
        'description': 'List blocks',
        'blocks': [
            ('add_to_list(item, list_name)', 'Add item to list'),
            ('delete_of_list(index, list_name)', 'Delete item at index'),
            ('delete_all_of_list(list_name)', 'Delete all items'),
            ('insert_at_list(index, item, list_name)', 'Insert item at index'),
            ('replace_item_of_list(index, item, list_name)', 'Replace item at index'),
            ('item_of_list(index, list_name)', 'Get item at index (reporter)'),
            ('item_num_of_list(item, list_name)', 'Get index of item (reporter)'),
            ('length_of_list(list_name)', 'Get list length (reporter)'),
            ('list_contains(list_name, item)', 'List contains item? (boolean)'),
            ('show_list(list_name)', 'Show list on stage'),
            ('hide_list(list_name)', 'Hide list from stage'),
        ]
    },
    'custom': {
        'description': 'Custom blocks (My Blocks)',
        'blocks': [
            ('def my_block(self, arg1, arg2):', 'Define a custom block'),
            ('self.my_block(value1, value2)', 'Call a custom block'),
        ]
    },
    'sprites': {
        'description': 'Creating and using sprites',
        'blocks': [
            ('class Cat:', 'Use official Scratch sprite (339 available)'),
            ('class MySprite:', 'Creates sprite with default costume'),
            ('class Player(Cat):', 'Inherit from library sprite'),
            ('', ''),
            ('# Multiple sprites example:', ''),
            ('class Cat:', '  First sprite'),
            ('    def when_flag_clicked(self):', ''),
            ('        say("I am the cat!")', ''),
            ('', ''),
            ('class Dog:', '  Second sprite'),
            ('    def when_flag_clicked(self):', ''),
            ('        say("I am the dog!")', ''),
            ('', ''),
            ('# List all available sprites:', ''),
            ('from scratch import list_sprites', ''),
            ('print(list_sprites())', 'Shows all 339 sprite names'),
        ]
    },
    'costumes': {
        'description': 'Adding costumes to sprites',
        'blocks': [
            ('class Cat:', 'Library sprites include all costumes'),
            ('', ''),
            ('# Costumes are automatically loaded for', ''),
            ('# library sprites like Cat, Dog, etc.', ''),
            ('', ''),
            ('switch_costume("costume2")', 'Switch to costume by name'),
            ('next_costume()', 'Switch to next costume'),
            ('costume_number()', 'Get current costume number'),
            ('costume_name()', 'Get current costume name'),
            ('', ''),
            ('# Example: Animation loop', ''),
            ('class Cat:', ''),
            ('    def when_flag_clicked(self):', ''),
            ('        while True:', ''),
            ('            next_costume()', ''),
            ('            wait(0.1)', ''),
            ('', ''),
            ('# Custom costumes with @sprite decorator:', ''),
            ('@sprite(costumes=[', ''),
            ('    Costume("idle", "sprites/idle.png"),', ''),
            ('    Costume("walk", "sprites/walk.png"),', ''),
            ('])', ''),
            ('class Player:', 'Sprite with custom costumes'),
        ]
    },
    'backdrops': {
        'description': 'Stage backdrops',
        'blocks': [
            ('switch_backdrop("backdrop1")', 'Switch backdrop by name'),
            ('next_backdrop()', 'Switch to next backdrop'),
            ('backdrop_number()', 'Get current backdrop number'),
            ('backdrop_name()', 'Get current backdrop name'),
            ('', ''),
            ('# Custom backdrops:', ''),
            ('configure_stage(backdrops=[', ''),
            ('    Backdrop("forest", "bg/forest.png"),', ''),
            ('    Backdrop("cave", "bg/cave.png"),', ''),
            ('])', ''),
            ('', ''),
            ('# Event: When backdrop switches', ''),
            ('def when_backdrop_forest(self):', 'Runs when backdrop = "forest"'),
        ]
    },
    'custom_assets': {
        'description': 'Custom sprites, costumes, sounds, and backdrops',
        'blocks': [
            ('# === Custom Sprite with Image Files ===', ''),
            ('@sprite(', ''),
            ('    costumes=[', ''),
            ('        Costume("idle", "player_idle.png"),', 'PNG image'),
            ('        Costume("run", "player_run.svg"),', 'SVG image'),
            ('    ],', ''),
            ('    sounds=[', ''),
            ('        Sound("jump", "sounds/jump.wav"),', 'WAV audio'),
            ('        Sound("music", "sounds/bg.mp3"),', 'MP3 audio'),
            ('    ],', ''),
            ('    x=-100, y=0, size=50', 'Position and size'),
            (')', ''),
            ('class Player:', ''),
            ('    def when_flag_clicked(self):', ''),
            ('        play_sound("jump")', ''),
            ('', ''),
            ('# === Custom Backdrops ===', ''),
            ('configure_stage(', ''),
            ('    backdrops=[', ''),
            ('        Backdrop("level1", "backgrounds/level1.png"),', ''),
            ('        Backdrop("level2", "backgrounds/level2.svg"),', ''),
            ('    ],', ''),
            ('    sounds=[', ''),
            ('        Sound("theme", "music/theme.mp3"),', ''),
            ('    ]', ''),
            (')', ''),
            ('', ''),
            ('# === Inline SVG ===', ''),
            ('Costume("circle", svg_string="<svg>...</svg>")', 'SVG string'),
            ('Backdrop("bg", svg_string="<svg>...</svg>")', 'SVG string'),
            ('', ''),
            ('# === Sprite Properties ===', ''),
            ('@sprite(x=100, y=-50)', 'Position'),
            ('@sprite(size=200)', 'Size (percent)'),
            ('@sprite(direction=180)', 'Direction (degrees)'),
            ('@sprite(visible=False)', 'Start hidden'),
            ('@sprite(rotation_style="left-right")', 'Rotation style'),
        ]
    },
    'quickstart': {
        'description': 'Quick start guide',
        'blocks': [
            ('# Minimal example:', ''),
            ('from scratch import create_scratch_file', ''),
            ('from scratch.dsl import *', ''),
            ('', ''),
            ('class Cat:', ''),
            ('    def when_flag_clicked(self):', ''),
            ('        say("Hello!")', ''),
            ('        move(10)', ''),
            ('', ''),
            ('create_scratch_file()', 'Creates <filename>.sb3'),
            ('', ''),
            ('# Or with custom output name:', ''),
            ('create_scratch_file("my_game.sb3")', ''),
            ('', ''),
            ('# Manual method:', ''),
            ('from scratch import transpile_to_json, save_sb3', ''),
            ('code = open("game.py").read()', ''),
            ('json_str = transpile_to_json(code)', ''),
            ('save_sb3(json_str, "game.sb3")', ''),
        ]
    },
}


def print_blocks(category=None):
    """Print block reference, optionally filtered by category."""
    categories = [category] if category else BLOCK_REFERENCE.keys()
    
    for cat in categories:
        if cat not in BLOCK_REFERENCE:
            print(f"Unknown category: {cat}")
            print(f"Available categories: {', '.join(BLOCK_REFERENCE.keys())}")
            return
        
        info = BLOCK_REFERENCE[cat]
        print(f"\n{'='*60}")
        print(f"  {cat.upper()} - {info['description']}")
        print(f"{'='*60}")
        
        for func, desc in info['blocks']:
            if func == '':
                print()  # Empty line for spacing
            else:
                print(f"  {func:<45} {desc}")
    
    if not category:
        print(f"\n{'='*60}")
        print("  Tip: Use 'scratch blocks <category>' for specific category")
        print(f"  Categories: {', '.join(BLOCK_REFERENCE.keys())}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        prog='scratch',
        description='Bidirectional Python to Scratch 3.0 transpiler'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # py2sb3 command
    py2sb3_parser = subparsers.add_parser(
        'py2sb3', 
        help='Convert Python file to Scratch .sb3'
    )
    py2sb3_parser.add_argument('input', help='Input Python file')
    py2sb3_parser.add_argument('output', nargs='?', help='Output .sb3 file (default: same name)')
    
    # sb32py command
    sb32py_parser = subparsers.add_parser(
        'sb32py',
        help='Convert Scratch .sb3 to Python file'
    )
    sb32py_parser.add_argument('input', help='Input .sb3 file')
    sb32py_parser.add_argument('output', nargs='?', help='Output Python file (default: same name)')
    
    # roundtrip command
    roundtrip_parser = subparsers.add_parser(
        'roundtrip',
        help='Round-trip conversion: .sb3 -> Python -> .sb3 (preserves assets)'
    )
    roundtrip_parser.add_argument('input', help='Input .sb3 file')
    roundtrip_parser.add_argument('output', nargs='?', help='Output .sb3 file (default: _roundtrip suffix)')
    roundtrip_parser.add_argument('--py', help='Also save intermediate Python file')
    
    # blocks command
    blocks_parser = subparsers.add_parser(
        'blocks',
        help='Show available Python functions and their Scratch blocks'
    )
    blocks_parser.add_argument(
        'category', 
        nargs='?', 
        help=f'Category to show ({", ".join(BLOCK_REFERENCE.keys())})'
    )
    
    # info command
    info_parser = subparsers.add_parser(
        'info',
        help='Show info about a .sb3 file'
    )
    info_parser.add_argument('input', help='Input .sb3 file')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    # Handle blocks command (no imports needed)
    if args.command == 'blocks':
        print_blocks(args.category)
        sys.exit(0)
    
    # Import here to avoid slow startup
    from . import transpile_to_json, save_sb3, convert_sb3_to_py, roundtrip_sb3
    
    try:
        if args.command == 'py2sb3':
            input_path = Path(args.input)
            output_path = args.output or str(input_path.with_suffix('.sb3'))
            base_path = str(input_path.parent.resolve())
            
            print(f"Converting: {input_path} -> {output_path}")
            
            with open(input_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            json_str, custom_assets = transpile_to_json(code, base_path=base_path)
            save_sb3(json_str, output_path, custom_assets=custom_assets)
            
        elif args.command == 'sb32py':
            input_path = args.input
            output_path = args.output
            
            convert_sb3_to_py(input_path, output_path)
            
        elif args.command == 'roundtrip':
            input_path = args.input
            output_path = args.output
            py_path = getattr(args, 'py', None)
            
            roundtrip_sb3(input_path, output_path, py_path)
            
        elif args.command == 'info':
            import zipfile
            import json
            
            with zipfile.ZipFile(args.input, 'r') as zf:
                project = json.loads(zf.read('project.json').decode('utf-8'))
                
                print(f"File: {args.input}")
                print(f"Sprites: {len([t for t in project['targets'] if not t.get('isStage')])}")
                
                for target in project['targets']:
                    name = target['name']
                    is_stage = target.get('isStage', False)
                    costumes = len(target.get('costumes', []))
                    sounds = len(target.get('sounds', []))
                    blocks = len(target.get('blocks', {}))
                    
                    prefix = "[Stage]" if is_stage else "[Sprite]"
                    print(f"  {prefix} {name}: {costumes} costumes, {sounds} sounds, {blocks} blocks")
                    
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
