"""
Python to Scratch 3.0 (sb3) Transpiler

Converts a subset of Python code into valid Scratch 3.0 project.json format
using the ast module to parse and walk the Abstract Syntax Tree.
"""

import ast
import uuid
import json
import zipfile
import hashlib
from typing import Dict, List, Any, Optional, Tuple

# Import sprite library for official Scratch assets
try:
    from .library import (
        get_sprite_data, get_costume_data_for_project, 
        get_sound_data_for_project, get_cached_asset,
        SPRITE_LIBRARY, find_sprite_by_name,
        get_library_sound_for_project, get_library_sound_data,
        find_sound_by_name, SOUNDS_LIBRARY, download_library_sound
    )
    SPRITE_LIBRARY_AVAILABLE = True
except ImportError:
    # Fallback for standalone use
    try:
        from sprite_library import (
            get_sprite_data, get_costume_data_for_project, 
            get_sound_data_for_project, get_cached_asset,
            SPRITE_LIBRARY, find_sprite_by_name,
            get_library_sound_for_project, get_library_sound_data,
            find_sound_by_name, SOUNDS_LIBRARY, download_library_sound
        )
        SPRITE_LIBRARY_AVAILABLE = True
    except ImportError:
        SPRITE_LIBRARY_AVAILABLE = False
        SPRITE_LIBRARY = {}
        SOUNDS_LIBRARY = {}


class ScratchTranspiler(ast.NodeVisitor):
    """
    AST NodeVisitor that transpiles Python code to Scratch 3.0 blocks.
    
    Supports class-based sprites: each Python class becomes a Scratch Sprite.
    
    Supported mappings:
        Motion:
        - move(steps)              -> motion_movesteps
        - turn_right(degrees)      -> motion_turnright
        - turn_left(degrees)       -> motion_turnleft
        - go_to(target)            -> motion_goto
        - go_to_xy(x, y)           -> motion_gotoxy
        - glide_to(secs, target)   -> motion_glideto
        - glide_to_xy(secs, x, y)  -> motion_glidesecstoxy
        - point_in_direction(dir)  -> motion_pointindirection
        - point_towards(target)    -> motion_pointtowards
        - change_x(dx)             -> motion_changexby
        - set_x(x)                 -> motion_setx
        - change_y(dy)             -> motion_changeyby
        - set_y(y)                 -> motion_sety
        - if_on_edge_bounce()      -> motion_ifonedgebounce
        - set_rotation_style(style)-> motion_setrotationstyle
        - x_position()             -> motion_xposition (reporter)
        - y_position()             -> motion_yposition (reporter)
        - direction()              -> motion_direction (reporter)
        
        Looks:
        - say(message)             -> looks_say
        - say_for_secs(msg, secs)  -> looks_sayforsecs
        - think(message)           -> looks_think
        - think_for_secs(msg,secs) -> looks_thinkforsecs
        - switch_costume(name)     -> looks_switchcostumeto
        - next_costume()           -> looks_nextcostume
        - switch_backdrop(name)    -> looks_switchbackdropto
        - next_backdrop()          -> looks_nextbackdrop
        - change_size(val)         -> looks_changesizeby
        - set_size(percent)        -> looks_setsizeto
        - change_effect(eff, val)  -> looks_changeeffectby
        - set_effect(effect, val)  -> looks_seteffectto
        - clear_effects()          -> looks_cleargraphiceffects
        - show()                   -> looks_show
        - hide()                   -> looks_hide
        - go_to_layer(layer)       -> looks_gotofrontback
        - change_layer(dir, num)   -> looks_goforwardbackwardlayers
        - costume_number()         -> looks_costumenumbername (reporter)
        - costume_name()           -> looks_costumenumbername (reporter)
        - backdrop_number()        -> looks_backdropnumbername (reporter)
        - backdrop_name()          -> looks_backdropnumbername (reporter)
        - size()                   -> looks_size (reporter)
        
        Sound:
        - play_sound(name)         -> sound_play
        - play_sound_until_done(n) -> sound_playuntildone
        - stop_all_sounds()        -> sound_stopallsounds
        - change_sound_effect(e,v) -> sound_changeeffectby
        - set_sound_effect(e,v)    -> sound_seteffectto
        - clear_sound_effects()    -> sound_cleareffects
        - change_volume(v)         -> sound_changevolumeby
        - set_volume(v)            -> sound_setvolumeto
        - volume()                 -> sound_volume (reporter)
        
        Events:
        - when_flag_clicked()      -> event_whenflagclicked (hat)
        - when_key_<key>()         -> event_whenkeypressed (hat)
        - when_clicked()           -> event_whenthisspriteclicked (hat)
        - when_backdrop_<name>()   -> event_whenbackdropswitchesto (hat)
        - when_broadcast_<msg>()   -> event_whenbroadcastreceived (hat)
        - broadcast(msg)           -> event_broadcast
        - broadcast_and_wait(msg)  -> event_broadcastandwait
        
        Control:
        - wait(secs)               -> control_wait
        - for i in range(n):       -> control_repeat
        - while True:              -> control_forever
        - while condition:         -> control_repeat_until
        - if condition:            -> control_if / control_if_else
        - stop("all")              -> control_stop
        - create_clone("myself")   -> control_create_clone_of
        - delete_this_clone()      -> control_delete_this_clone
        - when_i_start_as_clone()  -> control_start_as_clone (hat)
        
        Sensing:
        - touching(target)         -> sensing_touchingobject (boolean)
        - touching_color(color)    -> sensing_touchingcolor (boolean)
        - key_pressed(key)         -> sensing_keypressed (boolean)
        - mouse_down()             -> sensing_mousedown (boolean)
        - distance_to(target)      -> sensing_distanceto (reporter)
        - ask(question)            -> sensing_askandwait
        - answer()                 -> sensing_answer (reporter)
        - mouse_x()                -> sensing_mousex (reporter)
        - mouse_y()                -> sensing_mousey (reporter)
        - loudness()               -> sensing_loudness (reporter)
        - timer()                  -> sensing_timer (reporter)
        - reset_timer()            -> sensing_resettimer
        - current_year/month/etc() -> sensing_current (reporter)
        - days_since_2000()        -> sensing_dayssince2000 (reporter)
        - username()               -> sensing_username (reporter)
        
        Operators:
        - > < == != >= <=          -> operator_gt/lt/equals/not
        - + - * / %                -> operator_add/subtract/multiply/divide/mod
        - and or not               -> operator_and/or/not
        - random(from, to)         -> operator_random
        - join(s1, s2)             -> operator_join
        - letter_of(n, s)          -> operator_letter_of
        - length(s)                -> operator_length
        - contains(s1, s2)         -> operator_contains
        - round(n)                 -> operator_round
        - abs/floor/sqrt/sin/etc   -> operator_mathop
        
        Variables:
        - x = value                -> data_setvariableto
        - x += value               -> data_changevariableby
        - x (in expression)        -> data_variable (reporter)
        - show_variable(name)      -> data_showvariable
        - hide_variable(name)      -> data_hidevariable
        
        Lists:
        - add_to_list(item, name)  -> data_addtolist
        - delete_of_list(i, name)  -> data_deleteoflist
        - delete_all_of_list(name) -> data_deletealloflist
        - insert_at_list(i,v,name) -> data_insertatlist
        - replace_item_of_list()   -> data_replaceitemoflist
        - item_of_list(i, name)    -> data_itemoflist (reporter)
        - item_num_of_list(v,name) -> data_itemnumoflist (reporter)
        - length_of_list(name)     -> data_lengthoflist (reporter)
        - list_contains(name, v)   -> data_listcontainsitem (boolean)
        - show_list(name)          -> data_showlist
        - hide_list(name)          -> data_hidelist
    """
    
    # Simple function mappings: func_name -> (opcode, input_name)
    # These take exactly one argument
    FUNCTION_MAP = {
        # Motion - single argument
        'move': ('motion_movesteps', 'STEPS'),
        'turn_right': ('motion_turnright', 'DEGREES'),
        'turn_left': ('motion_turnleft', 'DEGREES'),
        'point_in_direction': ('motion_pointindirection', 'DIRECTION'),
        'change_x': ('motion_changexby', 'DX'),
        'set_x': ('motion_setx', 'X'),
        'change_y': ('motion_changeyby', 'DY'),
        'set_y': ('motion_sety', 'Y'),
        # Looks - single argument
        'say': ('looks_say', 'MESSAGE'),
        'think': ('looks_think', 'MESSAGE'),
        'change_size': ('looks_changesizeby', 'CHANGE'),
        'set_size': ('looks_setsizeto', 'SIZE'),
        # Control - single argument
        'wait': ('control_wait', 'DURATION'),
        # Sound - single argument
        'change_volume': ('sound_changevolumeby', 'VOLUME'),
        'set_volume': ('sound_setvolumeto', 'VOLUME'),
        'change_tempo': ('music_changeTempo', 'TEMPO'),
        'set_tempo': ('music_setTempo', 'TEMPO'),
        # Sensing - single argument
        'ask': ('sensing_askandwait', 'QUESTION'),
        'set_drag_mode': ('sensing_setdragmode', 'DRAG_MODE'),
    }
    
    # Multi-argument function mappings: func_name -> (opcode, [input_names])
    MULTI_ARG_MAP = {
        # Motion
        'go_to_xy': ('motion_gotoxy', ['X', 'Y']),
        'glide_to_xy': ('motion_glidesecstoxy', ['SECS', 'X', 'Y']),
        # Looks
        'say_for_secs': ('looks_sayforsecs', ['MESSAGE', 'SECS']),
        'think_for_secs': ('looks_thinkforsecs', ['MESSAGE', 'SECS']),
        # Control
        'create_clone_of': ('control_create_clone_of', ['CLONE_OPTION']),
        # Sensing - timer
        'reset_timer': ('sensing_resettimer', []),
    }
    
    # Field+Input function mappings: func_name -> (opcode, field_name, input_name, valid_field_values)
    # First arg is a string field, second arg is numeric input
    FIELD_INPUT_MAP = {
        'change_effect': ('looks_changeeffectby', 'EFFECT', 'CHANGE',
                          ['COLOR', 'FISHEYE', 'WHIRL', 'PIXELATE', 'MOSAIC', 'BRIGHTNESS', 'GHOST']),
        'set_effect': ('looks_seteffectto', 'EFFECT', 'VALUE',
                       ['COLOR', 'FISHEYE', 'WHIRL', 'PIXELATE', 'MOSAIC', 'BRIGHTNESS', 'GHOST']),
        'change_layer': ('looks_goforwardbackwardlayers', 'FORWARD_BACKWARD', 'NUM',
                         ['forward', 'backward']),
        # Sound effects
        'change_sound_effect': ('sound_changeeffectby', 'EFFECT', 'VALUE',
                                ['PITCH', 'PAN']),
        'set_sound_effect': ('sound_seteffectto', 'EFFECT', 'VALUE',
                             ['PITCH', 'PAN']),
    }
    
    # No-argument function mappings: func_name -> opcode
    NO_ARG_MAP = {
        # Motion
        'if_on_edge_bounce': 'motion_ifonedgebounce',
        # Looks
        'next_costume': 'looks_nextcostume',
        'next_backdrop': 'looks_nextbackdrop',
        'clear_effects': 'looks_cleargraphiceffects',
        'show': 'looks_show',
        'hide': 'looks_hide',
        # Control
        'delete_this_clone': 'control_delete_this_clone',
        # Sound
        'stop_all_sounds': 'sound_stopallsounds',
        'clear_sound_effects': 'sound_cleareffects',
        # Sensing
        'reset_timer': 'sensing_resettimer',
    }
    
    # Menu-based function mappings: func_name -> (opcode, input_name, menu_opcode, menu_field)
    # These have a dropdown menu for target selection
    MENU_FUNCTION_MAP = {
        'go_to': ('motion_goto', 'TO', 'motion_goto_menu', 'TO'),
        'glide_to': ('motion_glideto', 'TO', 'motion_glideto_menu', 'TO'),
        'point_towards': ('motion_pointtowards', 'TOWARDS', 'motion_pointtowards_menu', 'TOWARDS'),
        # Looks - costume/backdrop use menus
        'switch_costume': ('looks_switchcostumeto', 'COSTUME', 'looks_costume', 'COSTUME'),
        'switch_backdrop': ('looks_switchbackdropto', 'BACKDROP', 'looks_backdrops', 'BACKDROP'),
        # Sound - uses menus
        'play_sound': ('sound_play', 'SOUND_MENU', 'sound_sounds_menu', 'SOUND_MENU'),
        'start_sound': ('sound_play', 'SOUND_MENU', 'sound_sounds_menu', 'SOUND_MENU'),  # alias
        'play_sound_until_done': ('sound_playuntildone', 'SOUND_MENU', 'sound_sounds_menu', 'SOUND_MENU'),
        # Note: 'touching' is NOT here - it's a boolean reporter handled separately
        # Control - clone menu
        'create_clone': ('control_create_clone_of', 'CLONE_OPTION', 'control_create_clone_of_menu', 'CLONE_OPTION'),
    }
    
    # Field-based function mappings: func_name -> (opcode, field_name, valid_values)
    # These use fields instead of inputs (like rotation style)
    FIELD_FUNCTION_MAP = {
        'set_rotation_style': ('motion_setrotationstyle', 'STYLE', 
                               ['left-right', 'don\'t rotate', 'all around']),
        'go_to_layer': ('looks_gotofrontback', 'FRONT_BACK',
                        ['front', 'back']),
        # Control - stop block
        'stop': ('control_stop', 'STOP_OPTION', ['all', 'this script', 'other scripts in sprite']),
    }
    
    # Reporter functions (return values, used in expressions)
    REPORTER_MAP = {
        # Motion reporters
        'x_position': 'motion_xposition',
        'y_position': 'motion_yposition',
        'direction': 'motion_direction',
        # Looks reporters
        'size': 'looks_size',
        # Sensing reporters
        'mouse_x': 'sensing_mousex',
        'mouse_y': 'sensing_mousey',
        'loudness': 'sensing_loudness',
        'timer': 'sensing_timer',
        'days_since_2000': 'sensing_dayssince2000',
        'username': 'sensing_username',
        'answer': 'sensing_answer',
        # Sound reporters
        'volume': 'sound_volume',
    }
    
    # Boolean reporters (return True/False)
    BOOLEAN_REPORTER_MAP = {
        'mouse_down': 'sensing_mousedown',
    }
    
    # Special reporters that need fields (costume/backdrop number/name)
    FIELD_REPORTER_MAP = {
        'costume_number': ('looks_costumenumbername', 'NUMBER_NAME', 'number'),
        'costume_name': ('looks_costumenumbername', 'NUMBER_NAME', 'name'),
        'backdrop_number': ('looks_backdropnumbername', 'NUMBER_NAME', 'number'),
        'backdrop_name': ('looks_backdropnumbername', 'NUMBER_NAME', 'name'),
        # Sensing - current date/time
        'current_year': ('sensing_current', 'CURRENTMENU', 'YEAR'),
        'current_month': ('sensing_current', 'CURRENTMENU', 'MONTH'),
        'current_date': ('sensing_current', 'CURRENTMENU', 'DATE'),
        'current_day': ('sensing_current', 'CURRENTMENU', 'DAYOFWEEK'),
        'current_hour': ('sensing_current', 'CURRENTMENU', 'HOUR'),
        'current_minute': ('sensing_current', 'CURRENTMENU', 'MINUTE'),
        'current_second': ('sensing_current', 'CURRENTMENU', 'SECOND'),
    }
    
    # Mapping of Python comparison operators to Scratch opcodes
    COMPARE_MAP = {
        ast.Gt: 'operator_gt',
        ast.Lt: 'operator_lt',
        ast.Eq: 'operator_equals',
        # Note: Scratch doesn't have native !=, >=, <= 
        # We'll handle these with NOT and compound expressions
    }
    
    # Mapping of Python binary operators to Scratch opcodes
    BINOP_MAP = {
        ast.Add: 'operator_add',
        ast.Sub: 'operator_subtract',
        ast.Mult: 'operator_multiply',
        ast.Div: 'operator_divide',
        ast.Mod: 'operator_mod',
        ast.FloorDiv: 'operator_divide',  # Scratch doesn't have floor div, use regular
    }
    
    def __init__(self):
        self.blocks: Dict[str, Dict[str, Any]] = {}
        self.current_parent_id: Optional[str] = None
        self.previous_block_id: Optional[str] = None
        self.hat_block_id: Optional[str] = None
        
        # Variable tracking
        # Maps variable_name -> variable_id
        self.variable_ids: Dict[str, str] = {}
        # Scratch variable definitions: {"ID": ["Name", initial_value]}
        self.variable_definitions: Dict[str, List[Any]] = {}
        
        # Broadcast tracking
        # Maps broadcast_name -> broadcast_id
        self.broadcast_ids: Dict[str, str] = {}
        
        # List tracking
        # Maps list_name -> list_id  
        self.list_ids: Dict[str, str] = {}
        # Scratch list definitions: {"ID": ["Name", [items]]}
        self.list_definitions: Dict[str, List[Any]] = {}
        
        # Custom blocks (My Blocks / procedures) tracking
        # Maps procedure_name -> {proccode, argument_ids, argument_names, argument_defaults, warp}
        self.custom_blocks: Dict[str, Dict[str, Any]] = {}
        
        # Sound tracking - sounds used in code that need to be added to sprite
        self.sounds_used: set = set()
        
        # Multi-sprite support
        # List of all sprite targets: [{name, blocks, variables}, ...]
        self.targets: List[Dict[str, Any]] = []
        # Current sprite being processed
        self.current_sprite_name: Optional[str] = None
        # Stage blocks/variables (for code outside classes)
        self.stage_blocks: Dict[str, Dict[str, Any]] = {}
        self.stage_variables: Dict[str, List[Any]] = {}
    
    def _get_or_create_broadcast(self, name: str) -> str:
        """Get or create a broadcast ID for a message name."""
        if name not in self.broadcast_ids:
            self.broadcast_ids[name] = self._generate_id()
        return self.broadcast_ids[name]
    
    def _get_or_create_list(self, name: str, initial_items: List = None) -> str:
        """Get or create a list ID for a list name."""
        if name not in self.list_ids:
            list_id = self._generate_id()
            self.list_ids[name] = list_id
            # Store list definition
            self.list_definitions[list_id] = [name, initial_items or []]
        return self.list_ids[name]
    
    def _create_list_reporter(self, list_name: str) -> str:
        """
        Create a data_listcontents reporter block for a list.
        
        Args:
            list_name: Name of the list
            
        Returns:
            Block ID of the created reporter
        """
        list_id = self._get_or_create_list(list_name)
        
        reporter_id = self._generate_id()
        reporter_block = {
            "opcode": "data_listcontents",
            "next": None,
            "parent": None,
            "inputs": {},
            "fields": {
                "LIST": [list_name, list_id]
            },
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[reporter_id] = reporter_block
        return reporter_id
    
    def _create_custom_block_definition(self, node: ast.FunctionDef) -> None:
        """
        Create a custom block (My Block) definition from a Python function.
        
        The function name becomes the block name.
        Function parameters become block arguments.
        
        Example:
            def my_custom_block(self, steps, message):
                move(steps)
                say(message)
        
        Creates a "define my_custom_block" hat block with two arguments.
        """
        # Handle both "define_name" and "name" patterns
        proc_name = node.name.replace('define_', '')
        
        # Check if this was pre-registered
        preregistered = self.custom_blocks.get(proc_name, {}).get('_preregistered', False)
        
        if preregistered:
            # Use pre-registered argument info
            arg_names = self.custom_blocks[proc_name]["argument_names"]
            arg_ids = self.custom_blocks[proc_name]["argument_ids"]
            arg_defaults = self.custom_blocks[proc_name]["argument_defaults"]
            proccode = self.custom_blocks[proc_name]["proccode"]
        else:
            # Extract arguments (skip 'self' if present)
            args = node.args.args
            arg_names = []
            arg_ids = []
            arg_defaults = []
            
            for arg in args:
                if arg.arg != 'self':
                    arg_names.append(arg.arg)
                    arg_ids.append(self._generate_id())
                    arg_defaults.append("")  # Default value for arguments
            
            # Build proccode: "my_custom_block %s %s" for string/number args
            proccode = proc_name
            for _ in arg_names:
                proccode += " %s"  # All args are string/number for simplicity
        
        # Generate IDs for the definition and prototype blocks
        definition_id = self._generate_id()
        prototype_id = self._generate_id()
        
        # Create argument reporter blocks (these go in the prototype's inputs)
        argument_inputs = {}
        for i, (arg_name, arg_id) in enumerate(zip(arg_names, arg_ids)):
            # Create the argument reporter block
            arg_reporter_id = self._generate_id()
            arg_reporter = {
                "opcode": "argument_reporter_string_number",
                "next": None,
                "parent": prototype_id,
                "inputs": {},
                "fields": {
                    "VALUE": [arg_name, None]
                },
                "shadow": True,
                "topLevel": False,
            }
            self.blocks[arg_reporter_id] = arg_reporter
            argument_inputs[arg_id] = [1, arg_reporter_id]
        
        # Create the prototype block
        prototype = {
            "opcode": "procedures_prototype",
            "next": None,
            "parent": definition_id,
            "inputs": argument_inputs,
            "fields": {},
            "shadow": True,
            "topLevel": False,
            "mutation": {
                "tagName": "mutation",
                "children": [],
                "proccode": proccode,
                "argumentids": json.dumps(arg_ids),
                "argumentnames": json.dumps(arg_names),
                "argumentdefaults": json.dumps(arg_defaults),
                "warp": "false"
            }
        }
        self.blocks[prototype_id] = prototype
        
        # Create the definition block (hat block)
        definition = {
            "opcode": "procedures_definition",
            "next": None,
            "parent": None,
            "inputs": {
                "custom_block": [1, prototype_id]
            },
            "fields": {},
            "shadow": False,
            "topLevel": True,
            "x": 0,
            "y": len(self.custom_blocks) * 200  # Stack definitions vertically
        }
        self.blocks[definition_id] = definition
        
        # Store custom block info for later calls
        self.custom_blocks[proc_name] = {
            "proccode": proccode,
            "argument_ids": arg_ids,
            "argument_names": arg_names,
            "definition_id": definition_id,
            "prototype_id": prototype_id
        }
        
        # Set up the hat block context
        self.hat_block_id = definition_id
        self.previous_block_id = definition_id
        
        # Store argument name -> ID mapping for use in function body
        self._current_proc_args = dict(zip(arg_names, arg_ids))
        
        # Visit all statements in the function body
        for stmt in node.body:
            self.visit(stmt)
        
        # Clean up
        self._current_proc_args = {}
        self.previous_block_id = None
        self.hat_block_id = None
    
    def _create_procedure_call(self, proc_name: str, call_args: List[Any]) -> str:
        """
        Create a procedures_call block for calling a custom block.
        
        Args:
            proc_name: Name of the custom block
            call_args: List of argument values
            
        Returns:
            Block ID of the call block
        """
        if proc_name not in self.custom_blocks:
            return None
        
        proc_info = self.custom_blocks[proc_name]
        
        # Create the call block
        call_id = self._create_block(opcode='procedures_call', inputs={})
        
        # Build inputs for each argument
        inputs = {}
        for i, (arg_id, arg_val) in enumerate(zip(proc_info["argument_ids"], call_args)):
            inputs.update(self._create_literal_input(arg_val, arg_id, call_id))
        
        self.blocks[call_id]["inputs"] = inputs
        self.blocks[call_id]["mutation"] = {
            "tagName": "mutation",
            "children": [],
            "proccode": proc_info["proccode"],
            "argumentids": json.dumps(proc_info["argument_ids"]),
            "warp": "false"
        }
        
        return call_id
        
    def _generate_id(self) -> str:
        """Generate a unique block ID using uuid."""
        return str(uuid.uuid4()).replace('-', '')[:20]
    
    def _create_literal_input(self, value: Any, input_name: str, parent_block_id: str = None) -> Dict[str, Any]:
        """
        Create a Scratch input field for a literal value or variable reference.
        
        Scratch input format: [shadow_type, [value_type, value]]
        - Shadow type 1 = shadow (value block that can be replaced)
        - Shadow type 3 = block reference with shadow
        - Value type 4 = number, 10 = string
        
        For variables, we create a reporter block and reference it.
        """
        # Check if this is a variable reference (tuple marker from _extract_value)
        if isinstance(value, tuple) and len(value) == 2 and value[0] == '__VAR__':
            var_name = value[1]
            # Create a variable reporter block
            reporter_id = self._create_variable_reporter(var_name)
            # Set parent if provided
            if parent_block_id:
                self.blocks[reporter_id]["parent"] = parent_block_id
            # Return block reference format: [3, block_id, [default_value]]
            # Using [3, block_id, [4, "0"]] for a number with shadow
            return {input_name: [3, reporter_id, [4, "0"]]}
        elif isinstance(value, tuple) and len(value) == 2 and value[0] == '__BLOCK__':
            # This is a reference to an already-created block (e.g., BinOp result)
            block_id = value[1]
            if parent_block_id:
                self.blocks[block_id]["parent"] = parent_block_id
            return {input_name: [3, block_id, [4, "0"]]}
        elif isinstance(value, (int, float)):
            # Number input: [1, [4, "value"]]
            return {input_name: [1, [4, str(value)]]}
        else:
            # String input: [1, [10, "value"]]
            return {input_name: [1, [10, str(value)]]}
    
    def _get_or_create_variable(self, var_name: str, initial_value: Any = 0) -> str:
        """
        Get existing variable ID or create a new one.
        
        Args:
            var_name: The Python variable name
            initial_value: Initial value for the variable (default: 0)
            
        Returns:
            The unique variable ID
        """
        if var_name not in self.variable_ids:
            var_id = self._generate_id()
            self.variable_ids[var_name] = var_id
            # Scratch format: {"ID": ["Name", initial_value]}
            self.variable_definitions[var_id] = [var_name, initial_value]
        return self.variable_ids[var_name]
    
    def _create_variable_reporter(self, var_name: str) -> str:
        """
        Create a data_variable reporter block for reading a variable.
        
        Args:
            var_name: The variable name to read
            
        Returns:
            The block ID of the variable reporter
        """
        var_id = self._get_or_create_variable(var_name)
        
        block_id = self._generate_id()
        
        block = {
            "opcode": "data_variable",
            "next": None,
            "parent": None,
            "inputs": {},
            "fields": {
                "VARIABLE": [var_name, var_id]
            },
            "shadow": False,
            "topLevel": False,
        }
        
        self.blocks[block_id] = block
        return block_id
    
    def _create_block(self, opcode: str, inputs: Dict = None, 
                      top_level: bool = False, is_hat: bool = False,
                      is_reporter: bool = False) -> str:
        """
        Create a Scratch block and add it to the blocks dictionary.
        
        Args:
            opcode: The Scratch opcode (e.g., 'motion_movesteps')
            inputs: Dictionary of input fields
            top_level: Whether this block is at the top level (not nested)
            is_hat: Whether this is a hat block (event starter)
            is_reporter: Whether this is a reporter block (returns a value)
            
        Returns:
            The unique ID of the created block
        """
        block_id = self._generate_id()
        
        block = {
            "opcode": opcode,
            "next": None,
            "parent": None,
            "inputs": inputs or {},
            "fields": {},
            "shadow": False,
            "topLevel": top_level,
        }
        
        # Hat blocks need x, y coordinates
        if top_level:
            block["x"] = 0
            block["y"] = 0
        
        # Reporter blocks don't participate in the linked list
        if not is_reporter:
            # Link to previous block (linked list logic)
            if self.previous_block_id is not None:
                # Set this block's parent to the previous block
                block["parent"] = self.previous_block_id
                # Set the previous block's next to this block
                self.blocks[self.previous_block_id]["next"] = block_id
        
        self.blocks[block_id] = block
        
        # Update tracking for linked list (only for stack blocks)
        if not is_reporter:
            if not is_hat:
                self.previous_block_id = block_id
            else:
                # Hat block becomes the parent for following blocks
                self.hat_block_id = block_id
                self.previous_block_id = block_id
            
        return block_id
    
    def _visit_body(self, body: List[ast.AST], parent_id: str) -> Optional[str]:
        """
        Visit a list of statements (body of if/for) and return the first block's ID.
        
        This pauses the current linked list, processes the body, and returns
        the ID of the first block created so it can be used as a SUBSTACK.
        
        Args:
            body: List of AST statements to visit
            parent_id: The ID of the container block (if/for)
            
        Returns:
            The ID of the first block in the body, or None if body is empty
        """
        # Save current linked list state
        saved_previous = self.previous_block_id
        
        # Reset for the inner body - first block has no previous
        self.previous_block_id = None
        first_block_id = None
        
        for stmt in body:
            self.visit(stmt)
            
            # Capture the first block created
            if first_block_id is None and self.previous_block_id is not None:
                first_block_id = self.previous_block_id
                # Set the first block's parent to the container
                self.blocks[first_block_id]["parent"] = parent_id
        
        # Restore the linked list state (container block becomes previous)
        self.previous_block_id = saved_previous
        
        return first_block_id
    
    def visit_Compare(self, node: ast.Compare) -> str:
        """
        Visit a comparison expression and create an operator block.
        
        Handles: 
        - > (operator_gt), < (operator_lt), == (operator_equals)
        - != -> NOT(operator_equals)
        - >= -> NOT(operator_lt) or OR(operator_gt, operator_equals)
        - <= -> NOT(operator_gt) or OR(operator_lt, operator_equals)
        
        Returns:
            The block ID of the comparison operator block
        """
        if not node.ops or not node.comparators:
            return None
            
        # Get the operator type
        op_type = type(node.ops[0])
        
        # Extract left and right operands
        left_value = self._extract_value(node.left)
        right_value = self._extract_value(node.comparators[0])
        
        # Handle operators that need special treatment
        if op_type == ast.NotEq:
            # != becomes NOT(==)
            eq_block_id = self._create_block(opcode='operator_equals', inputs={}, is_reporter=True)
            inputs = {}
            inputs.update(self._create_literal_input(left_value, 'OPERAND1', eq_block_id))
            inputs.update(self._create_literal_input(right_value, 'OPERAND2', eq_block_id))
            self.blocks[eq_block_id]["inputs"] = inputs
            
            # Wrap in NOT
            not_block_id = self._create_block(opcode='operator_not', inputs={}, is_reporter=True)
            self.blocks[not_block_id]["inputs"]["OPERAND"] = [2, eq_block_id]
            self.blocks[eq_block_id]["parent"] = not_block_id
            return not_block_id
            
        elif op_type == ast.GtE:
            # >= becomes NOT(<)
            lt_block_id = self._create_block(opcode='operator_lt', inputs={}, is_reporter=True)
            inputs = {}
            inputs.update(self._create_literal_input(left_value, 'OPERAND1', lt_block_id))
            inputs.update(self._create_literal_input(right_value, 'OPERAND2', lt_block_id))
            self.blocks[lt_block_id]["inputs"] = inputs
            
            not_block_id = self._create_block(opcode='operator_not', inputs={}, is_reporter=True)
            self.blocks[not_block_id]["inputs"]["OPERAND"] = [2, lt_block_id]
            self.blocks[lt_block_id]["parent"] = not_block_id
            return not_block_id
            
        elif op_type == ast.LtE:
            # <= becomes NOT(>)
            gt_block_id = self._create_block(opcode='operator_gt', inputs={}, is_reporter=True)
            inputs = {}
            inputs.update(self._create_literal_input(left_value, 'OPERAND1', gt_block_id))
            inputs.update(self._create_literal_input(right_value, 'OPERAND2', gt_block_id))
            self.blocks[gt_block_id]["inputs"] = inputs
            
            not_block_id = self._create_block(opcode='operator_not', inputs={}, is_reporter=True)
            self.blocks[not_block_id]["inputs"]["OPERAND"] = [2, gt_block_id]
            self.blocks[gt_block_id]["parent"] = not_block_id
            return not_block_id
        
        # Standard operators
        if op_type not in self.COMPARE_MAP:
            return None
            
        opcode = self.COMPARE_MAP[op_type]
        
        # Create the comparison block first so we have its ID for parenting
        block_id = self._create_block(opcode=opcode, inputs={}, is_reporter=True)
        
        # Create inputs for OPERAND1 and OPERAND2 (pass block_id for variable parenting)
        inputs = {}
        inputs.update(self._create_literal_input(left_value, 'OPERAND1', block_id))
        inputs.update(self._create_literal_input(right_value, 'OPERAND2', block_id))
        
        # Update the block's inputs
        self.blocks[block_id]["inputs"] = inputs
        
        return block_id
    
    def visit_BinOp(self, node: ast.BinOp) -> str:
        """
        Visit a binary operation and create an operator block.
        
        Handles: + (operator_add), - (operator_subtract), 
                 * (operator_multiply), / (operator_divide), % (operator_mod)
        
        Returns:
            The block ID of the operator block
        """
        op_type = type(node.op)
        
        if op_type not in self.BINOP_MAP:
            return None
            
        opcode = self.BINOP_MAP[op_type]
        
        # Extract left and right operands
        left_value = self._extract_value(node.left)
        right_value = self._extract_value(node.right)
        
        # Create the operator block first so we have its ID for parenting
        block_id = self._create_block(opcode=opcode, inputs={}, is_reporter=True)
        
        # Create inputs for NUM1 and NUM2 (math operators use NUM1/NUM2)
        inputs = {}
        inputs.update(self._create_literal_input(left_value, 'NUM1', block_id))
        inputs.update(self._create_literal_input(right_value, 'NUM2', block_id))
        
        # Update the block's inputs
        self.blocks[block_id]["inputs"] = inputs
        
        return block_id
    
    def visit_BoolOp(self, node: ast.BoolOp) -> str:
        """
        Visit a boolean operation and create an operator block.
        
        Handles: and (operator_and), or (operator_or)
        
        Note: These are binary in Scratch but can be chained in Python.
        For x and y and z, we create nested (x and (y and z)).
        
        Returns:
            The block ID of the operator block
        """
        if isinstance(node.op, ast.And):
            opcode = 'operator_and'
        elif isinstance(node.op, ast.Or):
            opcode = 'operator_or'
        else:
            return None
        
        # Process all operands - Scratch's and/or are binary, Python's can have multiple
        # We need to chain them: a and b and c -> (a and (b and c))
        values = node.values
        
        if len(values) < 2:
            return None
        
        # Process right-to-left to create proper nesting
        # Start with last two operands
        right_id = self._process_condition(values[-1])
        
        # Work backwards through the operands
        for i in range(len(values) - 2, -1, -1):
            left_id = self._process_condition(values[i])
            
            # Create the boolean operator block
            block_id = self._create_block(opcode=opcode, inputs={}, is_reporter=True)
            
            # Set OPERAND1 (left) and OPERAND2 (right)
            if left_id:
                self.blocks[block_id]["inputs"]["OPERAND1"] = [2, left_id]
                self.blocks[left_id]["parent"] = block_id
            if right_id:
                self.blocks[block_id]["inputs"]["OPERAND2"] = [2, right_id]
                self.blocks[right_id]["parent"] = block_id
            
            # This block becomes the right operand for the next iteration
            right_id = block_id
        
        return right_id

    def _extract_value(self, node: ast.AST) -> Any:
        """
        Extract a value from an AST node - handles literals, variables, and expressions.
        
        Returns a marker tuple for special values, or the literal value directly.
        """
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
            return node.n
        elif isinstance(node, ast.Str):  # Python < 3.8 compatibility
            return node.s
        elif isinstance(node, ast.UnaryOp):
            # Handle negative numbers: -10 is UnaryOp(op=USub, operand=Constant(10))
            if isinstance(node.op, ast.USub):
                operand_value = self._extract_value(node.operand)
                if isinstance(operand_value, (int, float)):
                    return -operand_value
            elif isinstance(node.op, ast.UAdd):
                return self._extract_value(node.operand)
            return 0
        elif isinstance(node, ast.Name):
            # This is a variable reference - return a special marker
            return ('__VAR__', node.id)
        elif isinstance(node, ast.BinOp):
            # This is a binary operation - create the block and return a reference
            block_id = self.visit_BinOp(node)
            return ('__BLOCK__', block_id)
        elif isinstance(node, ast.Call):
            # This could be a reporter function like x_position(), pick_random(), etc.
            # Try to visit it as a call - if it returns a block_id, use that
            block_id = self.visit_Call(node)
            if block_id:
                return ('__BLOCK__', block_id)
            return 0
        else:
            return 0

    def visit_Assign(self, node: ast.Assign) -> None:
        """
        Visit an assignment statement and create a data_setvariableto block.
        
        Handles: x = 10, x = "hello", x = y
        """
        # Get the target variable name (handle simple assignments only)
        if not node.targets or not isinstance(node.targets[0], ast.Name):
            return
        
        var_name = node.targets[0].id
        
        # Extract the value being assigned
        value = self._extract_value(node.value)
        
        # Determine initial value for variable definition
        # Use 0 as default for any non-literal values
        if isinstance(value, tuple):
            initial_value = 0  # Variable, block reference, or expression
        elif isinstance(value, (int, float)):
            initial_value = value
        elif isinstance(value, str):
            initial_value = value
        else:
            initial_value = 0
        
        # Get or create the variable ID
        var_id = self._get_or_create_variable(var_name, initial_value)
        
        # Create the set variable block
        block_id = self._create_block(opcode='data_setvariableto', inputs={})
        
        # Create the VALUE input (pass block_id for variable parenting)
        value_input = self._create_literal_input(value, 'VALUE', block_id)
        self.blocks[block_id]["inputs"] = value_input
        
        # Set the VARIABLE field (this is in fields, not inputs!)
        self.blocks[block_id]["fields"] = {
            "VARIABLE": [var_name, var_id]
        }
    
    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """
        Visit an augmented assignment statement (+=, -=, etc.)
        
        Handles: x += value -> data_changevariableby
        For other operators, falls back to set variable with expression.
        """
        # Only handle simple variable targets
        if not isinstance(node.target, ast.Name):
            return
        
        var_name = node.target.id
        
        # Extract the value
        value = self._extract_value(node.value)
        
        # Get or create the variable ID
        var_id = self._get_or_create_variable(var_name, 0)
        
        # For += with Add operator, use data_changevariableby
        if isinstance(node.op, ast.Add):
            block_id = self._create_block(opcode='data_changevariableby', inputs={})
            
            # Create the VALUE input
            value_input = self._create_literal_input(value, 'VALUE', block_id)
            self.blocks[block_id]["inputs"] = value_input
            
            # Set the VARIABLE field
            self.blocks[block_id]["fields"] = {
                "VARIABLE": [var_name, var_id]
            }
        elif isinstance(node.op, ast.Sub):
            # For -=, use change by negative value
            block_id = self._create_block(opcode='data_changevariableby', inputs={})
            
            # For literal numbers, negate them
            if isinstance(value, (int, float)):
                value = -value
                value_input = self._create_literal_input(value, 'VALUE', block_id)
            elif isinstance(value, tuple) and value[0] == '__BLOCK__':
                # For block references, wrap in operator_subtract from 0
                subtract_id = self._create_block(opcode='operator_subtract', inputs={}, is_reporter=True)
                self.blocks[subtract_id]["inputs"]["NUM1"] = [1, [4, "0"]]
                self.blocks[subtract_id]["inputs"]["NUM2"] = [3, value[1], [4, "0"]]
                self.blocks[value[1]]["parent"] = subtract_id
                value_input = {"VALUE": [3, subtract_id, [4, "0"]]}
            else:
                value_input = self._create_literal_input(value, 'VALUE', block_id)
            
            self.blocks[block_id]["inputs"] = value_input
            self.blocks[block_id]["fields"] = {
                "VARIABLE": [var_name, var_id]
            }
        else:
            # For other operators, use set variable with expression
            # This handles *=, /=, etc. by computing var op value
            pass  # TODO: implement full expression evaluation
    
    def visit_For(self, node: ast.For) -> None:
        """
        Visit a for loop and create a control_repeat block.
        
        Handles: for i in range(n): -> control_repeat with TIMES=n
        """
        # Check if this is a range() call
        times = 10  # Default
        
        if isinstance(node.iter, ast.Call):
            if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                if node.iter.args:
                    times = self._extract_value(node.iter.args[0])
        
        # Create the control_repeat block with TIMES input
        inputs = self._create_literal_input(times, 'TIMES')
        
        # Create the repeat block (it joins the current linked list)
        repeat_block_id = self._create_block(opcode='control_repeat', inputs=inputs)
        
        # Visit the body and get the first inner block's ID
        first_inner_id = self._visit_body(node.body, repeat_block_id)
        
        # Set the SUBSTACK input to point to the first inner block
        if first_inner_id:
            # SUBSTACK format: [2, block_id] where 2 means "block reference"
            self.blocks[repeat_block_id]["inputs"]["SUBSTACK"] = [2, first_inner_id]
        
        # The repeat block is now the previous block for anything that follows
        self.previous_block_id = repeat_block_id
    
    def visit_While(self, node: ast.While) -> None:
        """
        Visit a while loop and create control_forever or control_repeat_until.
        
        Handles:
        - while True:              -> control_forever (no next block allowed)
        - while condition:         -> control_repeat_until
        - while not condition:     -> control_wait_until (if just waiting)
        """
        # Check if this is "while True:" -> forever loop
        is_forever = False
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            is_forever = True
        elif isinstance(node.test, ast.NameConstant) and node.test.value is True:  # Python < 3.8
            is_forever = True
        
        if is_forever:
            # Create control_forever block
            forever_block_id = self._create_block(opcode='control_forever', inputs={})
            
            # Visit the body
            first_inner_id = self._visit_body(node.body, forever_block_id)
            
            if first_inner_id:
                self.blocks[forever_block_id]["inputs"]["SUBSTACK"] = [2, first_inner_id]
            
            # Forever blocks don't have a "next" - they run... forever
            # So we DON'T set previous_block_id (nothing can follow)
            self.previous_block_id = None  # Cap block - nothing can follow
        else:
            # Create control_repeat_until block
            repeat_until_id = self._create_block(opcode='control_repeat_until', inputs={})
            
            # Process the condition
            condition_block_id = self._process_condition(node.test)
            
            if condition_block_id:
                self.blocks[repeat_until_id]["inputs"]["CONDITION"] = [2, condition_block_id]
                self.blocks[condition_block_id]["parent"] = repeat_until_id
            
            # Visit the body
            first_inner_id = self._visit_body(node.body, repeat_until_id)
            
            if first_inner_id:
                self.blocks[repeat_until_id]["inputs"]["SUBSTACK"] = [2, first_inner_id]
            
            self.previous_block_id = repeat_until_id
    
    def _process_condition(self, node: ast.AST) -> Optional[str]:
        """
        Process a condition expression and return the block ID.
        
        Handles:
        - Compare: x > 5, x == y, etc.
        - BoolOp: x and y, x or y
        - UnaryOp: not x
        - Call: touching("mouse"), key_pressed("space")
        - Constant: True, False
        - Name: variable
        """
        if isinstance(node, ast.Compare):
            return self.visit_Compare(node)
        elif isinstance(node, ast.BoolOp):
            return self.visit_BoolOp(node)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            # not condition -> operator_not
            operand_id = self._process_condition(node.operand)
            not_block_id = self._create_block(opcode='operator_not', inputs={}, is_reporter=True)
            if operand_id:
                self.blocks[not_block_id]["inputs"]["OPERAND"] = [2, operand_id]
                self.blocks[operand_id]["parent"] = not_block_id
            return not_block_id
        elif isinstance(node, ast.Call):
            # Could be touching(), key_pressed(), mouse_down(), etc.
            return self.visit_Call(node)
        elif isinstance(node, ast.Constant):
            # Handle True/False constants
            # In Scratch, we can't really have a "true" block, so we use a comparison that's always true/false
            # True -> (1 = 1), False -> (1 = 0)
            if node.value is True:
                # Create "1 = 1" which is always true
                block_id = self._create_block(opcode='operator_equals', inputs={}, is_reporter=True)
                self.blocks[block_id]["inputs"]["OPERAND1"] = [1, [10, "1"]]
                self.blocks[block_id]["inputs"]["OPERAND2"] = [1, [10, "1"]]
                return block_id
            elif node.value is False:
                # Create "1 = 0" which is always false
                block_id = self._create_block(opcode='operator_equals', inputs={}, is_reporter=True)
                self.blocks[block_id]["inputs"]["OPERAND1"] = [1, [10, "1"]]
                self.blocks[block_id]["inputs"]["OPERAND2"] = [1, [10, "0"]]
                return block_id
        elif isinstance(node, ast.NameConstant):  # Python < 3.8 compatibility
            if node.value is True:
                block_id = self._create_block(opcode='operator_equals', inputs={}, is_reporter=True)
                self.blocks[block_id]["inputs"]["OPERAND1"] = [1, [10, "1"]]
                self.blocks[block_id]["inputs"]["OPERAND2"] = [1, [10, "1"]]
                return block_id
            elif node.value is False:
                block_id = self._create_block(opcode='operator_equals', inputs={}, is_reporter=True)
                self.blocks[block_id]["inputs"]["OPERAND1"] = [1, [10, "1"]]
                self.blocks[block_id]["inputs"]["OPERAND2"] = [1, [10, "0"]]
                return block_id
        return None

    def visit_If(self, node: ast.If) -> None:
        """
        Visit an if statement and create a control_if block.
        
        Handles: if condition: -> control_if with CONDITION and SUBSTACK
        Supports all boolean expressions via _process_condition.
        """
        # Process the condition using the general condition processor
        condition_block_id = self._process_condition(node.test)
        
        # Create the control_if block
        inputs = {}
        
        # Create the if block (it joins the current linked list)
        if_block_id = self._create_block(opcode='control_if', inputs=inputs)
        
        # Link the condition block to the if block
        if condition_block_id:
            # CONDITION format: [2, block_id] for boolean input
            self.blocks[if_block_id]["inputs"]["CONDITION"] = [2, condition_block_id]
            # Set the condition block's parent to the if block
            self.blocks[condition_block_id]["parent"] = if_block_id
        
        # Visit the body and get the first inner block's ID
        first_inner_id = self._visit_body(node.body, if_block_id)
        
        # Set the SUBSTACK input to point to the first inner block
        if first_inner_id:
            self.blocks[if_block_id]["inputs"]["SUBSTACK"] = [2, first_inner_id]
        
        # Handle else clause (SUBSTACK2) if present
        if node.orelse:
            # Change opcode to control_if_else
            self.blocks[if_block_id]["opcode"] = "control_if_else"
            
            first_else_id = self._visit_body(node.orelse, if_block_id)
            
            if first_else_id:
                self.blocks[if_block_id]["inputs"]["SUBSTACK2"] = [2, first_else_id]
        
        # The if block is now the previous block for anything that follows
        self.previous_block_id = if_block_id
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Visit a class definition - each class becomes a Scratch Sprite.
        
        The class name becomes the sprite name.
        Methods inside the class become scripts for that sprite.
        """
        sprite_name = node.name
        
        # Save any current state
        saved_blocks = self.blocks
        saved_variables = self.variable_definitions
        saved_var_ids = self.variable_ids
        saved_previous = self.previous_block_id
        saved_hat = self.hat_block_id
        saved_custom_blocks = self.custom_blocks
        
        # Reset state for this sprite
        self.blocks = {}
        self.variable_definitions = {}
        self.variable_ids = {}
        self.list_definitions = {}
        self.list_ids = {}
        self.custom_blocks = {}
        self._current_proc_args = {}
        self.sounds_used = set()
        self.previous_block_id = None
        self.hat_block_id = None
        self.current_sprite_name = sprite_name
        
        # TWO-PASS processing for custom blocks:
        # Pass 1: Pre-register all custom block definitions
        # This allows calls to custom blocks that are defined later in the class
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_name = item.name
                # Check if this looks like a custom block definition
                if not method_name.startswith('when_') and not method_name.startswith('__'):
                    # Pre-register the custom block (without generating code yet)
                    proc_name = method_name.replace('define_', '')
                    # Get argument names (skip 'self')
                    arg_names = [arg.arg for arg in item.args.args if arg.arg != 'self']
                    arg_ids = [self._generate_id() for _ in arg_names]
                    arg_defaults = [""] * len(arg_names)
                    
                    # Build proccode with %s placeholders
                    proccode = proc_name
                    if arg_names:
                        proccode += " " + " ".join(f"%s" for _ in arg_names)
                    
                    # Pre-register (definition blocks will be created in pass 2)
                    self.custom_blocks[proc_name] = {
                        "proccode": proccode,
                        "argument_ids": arg_ids,
                        "argument_names": arg_names,
                        "argument_defaults": arg_defaults,
                        "definition_id": None,  # Will be set in pass 2
                        "prototype_id": None,   # Will be set in pass 2
                        "_preregistered": True
                    }
        
        # Pass 2: Visit all methods in the class
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self._visit_sprite_method(item)
        
        # Store this sprite's data
        self.targets.append({
            'name': sprite_name,
            'blocks': self.blocks,
            'variables': self.variable_definitions,
            'lists': self.list_definitions,
            'broadcasts': self.broadcast_ids.copy(),
            'sounds_used': self.sounds_used.copy(),
        })
        
        # Restore previous state (for any code outside classes)
        self.blocks = saved_blocks
        self.variable_definitions = saved_variables
        self.variable_ids = saved_var_ids
        self.previous_block_id = saved_previous
        self.hat_block_id = saved_hat
        self.custom_blocks = saved_custom_blocks
        self.current_sprite_name = None
    
    def _visit_sprite_method(self, node: ast.FunctionDef) -> None:
        """
        Visit a method inside a sprite class.
        
        Handles hat blocks like when_flag_clicked, when_key_pressed, etc.
        """
        # Skip 'self' in method signature - it's just a Python convention
        
        if node.name == 'when_flag_clicked':
            # Create the hat block (event_whenflagclicked)
            self._create_block(
                opcode='event_whenflagclicked',
                top_level=True,
                is_hat=True
            )
            
            # Visit all statements in the function body
            for stmt in node.body:
                self.visit(stmt)
                
            # Reset for potential next script
            self.previous_block_id = None
            self.hat_block_id = None
            
        elif node.name.startswith('when_key_'):
            # when_key_space, when_key_up, when_key_a, etc.
            # Extract the key from the method name
            key = node.name[9:]  # Remove 'when_key_' prefix
            key_map = {
                'space': 'space', 'up': 'up arrow', 'down': 'down arrow',
                'left': 'left arrow', 'right': 'right arrow', 'any': 'any',
            }
            key_value = key_map.get(key, key)  # Default to the key name itself
            
            block_id = self._create_block(
                opcode='event_whenkeypressed',
                top_level=True,
                is_hat=True
            )
            self.blocks[block_id]["fields"]["KEY_OPTION"] = [key_value, None]
            
            for stmt in node.body:
                self.visit(stmt)
            
            self.previous_block_id = None
            self.hat_block_id = None
            
        elif node.name == 'when_i_start_as_clone':
            # Clone start event
            self._create_block(
                opcode='control_start_as_clone',
                top_level=True,
                is_hat=True
            )
            
            for stmt in node.body:
                self.visit(stmt)
            
            self.previous_block_id = None
            self.hat_block_id = None
            
        elif node.name == 'when_clicked':
            # When this sprite clicked
            self._create_block(
                opcode='event_whenthisspriteclicked',
                top_level=True,
                is_hat=True
            )
            
            for stmt in node.body:
                self.visit(stmt)
            
            self.previous_block_id = None
            self.hat_block_id = None
            
        elif node.name.startswith('when_backdrop_'):
            # when_backdrop_backdrop1, etc.
            backdrop_name = node.name[14:]  # Remove 'when_backdrop_' prefix
            
            block_id = self._create_block(
                opcode='event_whenbackdropswitchesto',
                top_level=True,
                is_hat=True
            )
            self.blocks[block_id]["fields"]["BACKDROP"] = [backdrop_name, None]
            
            for stmt in node.body:
                self.visit(stmt)
            
            self.previous_block_id = None
            self.hat_block_id = None
            
        elif node.name.startswith('when_broadcast_'):
            # when_broadcast_message1 -> event_whenbroadcastreceived
            message_name = node.name[15:]  # Remove 'when_broadcast_' prefix
            
            # Get or create broadcast ID
            broadcast_id = self._get_or_create_broadcast(message_name)
            
            block_id = self._create_block(
                opcode='event_whenbroadcastreceived',
                top_level=True,
                is_hat=True
            )
            self.blocks[block_id]["fields"]["BROADCAST_OPTION"] = [message_name, broadcast_id]
            
            for stmt in node.body:
                self.visit(stmt)
            
            self.previous_block_id = None
            self.hat_block_id = None
            
        elif node.name.startswith('when_loudness_gt_'):
            # when_loudness_gt_10 -> event_whengreaterthan with LOUDNESS
            threshold = node.name[17:]  # Remove 'when_loudness_gt_' prefix
            try:
                threshold_val = int(threshold)
            except ValueError:
                threshold_val = 10
            
            block_id = self._create_block(
                opcode='event_whengreaterthan',
                top_level=True,
                is_hat=True
            )
            self.blocks[block_id]["fields"]["WHENGREATERTHANMENU"] = ["LOUDNESS", None]
            self.blocks[block_id]["inputs"]["VALUE"] = [1, [4, str(threshold_val)]]
            
            for stmt in node.body:
                self.visit(stmt)
            
            self.previous_block_id = None
            self.hat_block_id = None
            
        elif node.name.startswith('when_timer_gt_'):
            # when_timer_gt_10 -> event_whengreaterthan with TIMER
            threshold = node.name[14:]
            try:
                threshold_val = float(threshold)
            except ValueError:
                threshold_val = 10
            
            block_id = self._create_block(
                opcode='event_whengreaterthan',
                top_level=True,
                is_hat=True
            )
            self.blocks[block_id]["fields"]["WHENGREATERTHANMENU"] = ["TIMER", None]
            self.blocks[block_id]["inputs"]["VALUE"] = [1, [4, str(threshold_val)]]
            
            for stmt in node.body:
                self.visit(stmt)
            
            self.previous_block_id = None
            self.hat_block_id = None
            
        elif not node.name.startswith('when_') and not node.name.startswith('__'):
            # This is a custom block definition (My Block)
            self._create_custom_block_definition(node)
        # Add more hat blocks here as needed
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        Visit a function definition (outside of a class).
        
        If the function is named 'when_flag_clicked', create a hat block
        and process the function body as the script.
        Code outside classes goes to a default sprite.
        """
        if node.name == 'when_flag_clicked':
            # Create the hat block (event_whenflagclicked)
            self._create_block(
                opcode='event_whenflagclicked',
                top_level=True,
                is_hat=True
            )
            
            # Visit all statements in the function body
            for stmt in node.body:
                self.visit(stmt)
                
            # Reset for potential next script
            self.previous_block_id = None
            self.hat_block_id = None
        else:
            # For other functions, just continue visiting
            self.generic_visit(node)
    
    def visit_Expr(self, node: ast.Expr) -> None:
        """Visit an expression statement (like a function call on its own line)."""
        self.visit(node.value)
    
    def _create_menu_block(self, menu_opcode: str, field_name: str, 
                           value: str, parent_id: str) -> str:
        """
        Create a menu block (shadow block for dropdowns).
        
        Args:
            menu_opcode: The menu's opcode (e.g., 'motion_goto_menu')
            field_name: The field name (e.g., 'TO')
            value: The selected value (e.g., '_random_', '_mouse_')
            parent_id: The parent block's ID
            
        Returns:
            The menu block's ID
        """
        menu_id = self._generate_id()
        
        menu_block = {
            "opcode": menu_opcode,
            "next": None,
            "parent": parent_id,
            "inputs": {},
            "fields": {
                field_name: [value, None]
            },
            "shadow": True,
            "topLevel": False,
        }
        
        self.blocks[menu_id] = menu_block
        return menu_id
    
    def _handle_motion_target(self, target_str: str) -> str:
        """
        Convert Python target strings to Scratch target values.
        
        Args:
            target_str: Python string like 'random', 'mouse', or sprite name
            
        Returns:
            Scratch target value like '_random_', '_mouse_', or sprite name
        """
        target_map = {
            'random': '_random_',
            'random_position': '_random_',
            'mouse': '_mouse_',
            'mouse_pointer': '_mouse_',
        }
        return target_map.get(target_str.lower(), target_str)
    
    def visit_Call(self, node: ast.Call) -> Any:
        """
        Visit a function call and convert to appropriate Scratch block.
        
        Handles all motion blocks, looks blocks, and other mapped functions.
        Returns block_id for reporter functions, None otherwise.
        """
        # Get the function name
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Handle method calls like self.mouse_down()
            func_name = node.func.attr
        else:
            # Unknown function type
            return None
        
        # === Reporter functions (return a value) ===
        if func_name in self.REPORTER_MAP:
            opcode = self.REPORTER_MAP[func_name]
            block_id = self._create_block(opcode=opcode, inputs={}, is_reporter=True)
            return block_id
        
        # === Boolean reporter functions (return True/False) ===
        if func_name in self.BOOLEAN_REPORTER_MAP:
            opcode = self.BOOLEAN_REPORTER_MAP[func_name]
            block_id = self._create_block(opcode=opcode, inputs={}, is_reporter=True)
            return block_id
        
        # === Field-based reporters (costume_number, backdrop_number, etc.) ===
        if func_name in self.FIELD_REPORTER_MAP:
            opcode, field_name, field_value = self.FIELD_REPORTER_MAP[func_name]
            block_id = self._create_block(opcode=opcode, inputs={}, is_reporter=True)
            self.blocks[block_id]["fields"][field_name] = [field_value, None]
            return block_id
        
        # === Simple single-argument functions ===
        if func_name in self.FUNCTION_MAP:
            opcode, input_name = self.FUNCTION_MAP[func_name]
            
            # Create the block first so we have its ID
            block_id = self._create_block(opcode=opcode, inputs={})
            
            # Get the argument value and create input
            if node.args:
                arg = node.args[0]
                value = self._extract_value(arg)
                inputs = self._create_literal_input(value, input_name, block_id)
                self.blocks[block_id]["inputs"] = inputs
            return None
        
        # === Multi-argument functions ===
        if func_name in self.MULTI_ARG_MAP:
            opcode, input_names = self.MULTI_ARG_MAP[func_name]
            
            # Create the block
            block_id = self._create_block(opcode=opcode, inputs={})
            
            # Process each argument
            inputs = {}
            for i, input_name in enumerate(input_names):
                if i < len(node.args):
                    value = self._extract_value(node.args[i])
                    inputs.update(self._create_literal_input(value, input_name, block_id))
            
            self.blocks[block_id]["inputs"] = inputs
            return None
        
        # === No-argument functions ===
        if func_name in self.NO_ARG_MAP:
            opcode = self.NO_ARG_MAP[func_name]
            self._create_block(opcode=opcode, inputs={})
            return None
        
        # === Field+Input functions (effect blocks, layer changes) ===
        if func_name in self.FIELD_INPUT_MAP:
            opcode, field_name, input_name, valid_values = self.FIELD_INPUT_MAP[func_name]
            
            # Create the block
            block_id = self._create_block(opcode=opcode, inputs={})
            
            # First arg is the field value (string)
            if len(node.args) >= 1:
                field_value = self._extract_value(node.args[0])
                if isinstance(field_value, str):
                    field_value = field_value.upper()  # Scratch expects uppercase effect names
                self.blocks[block_id]["fields"][field_name] = [field_value, None]
            
            # Second arg is the input value (number)
            if len(node.args) >= 2:
                input_value = self._extract_value(node.args[1])
                inputs = self._create_literal_input(input_value, input_name, block_id)
                self.blocks[block_id]["inputs"] = inputs
            
            return None
        
        # === Menu-based functions (go_to, glide_to, point_towards) ===
        if func_name in self.MENU_FUNCTION_MAP:
            opcode, input_name, menu_opcode, menu_field = self.MENU_FUNCTION_MAP[func_name]
            
            # For glide_to, first arg is SECS, second is target
            if func_name == 'glide_to':
                # Create the main block
                block_id = self._create_block(opcode=opcode, inputs={})
                
                # First arg is SECS
                if len(node.args) >= 1:
                    secs_value = self._extract_value(node.args[0])
                    secs_input = self._create_literal_input(secs_value, 'SECS', block_id)
                    self.blocks[block_id]["inputs"].update(secs_input)
                
                # Second arg is target
                if len(node.args) >= 2:
                    target_value = self._extract_value(node.args[1])
                    if isinstance(target_value, str):
                        target_value = self._handle_motion_target(target_value)
                    
                    menu_id = self._create_menu_block(menu_opcode, menu_field,
                                                      str(target_value), block_id)
                    self.blocks[block_id]["inputs"][input_name] = [1, menu_id]
            else:
                # go_to, point_towards, play_sound, etc. - single target argument
                block_id = self._create_block(opcode=opcode, inputs={})
                
                if node.args:
                    target_value = self._extract_value(node.args[0])
                    if isinstance(target_value, str):
                        # For motion blocks, handle special targets
                        if func_name in ('go_to', 'point_towards'):
                            target_value = self._handle_motion_target(target_value)
                        # For sound blocks, track the sound name
                        elif func_name in ('play_sound', 'start_sound', 'play_sound_until_done'):
                            self.sounds_used.add(target_value)
                    
                    menu_id = self._create_menu_block(menu_opcode, menu_field,
                                                      str(target_value), block_id)
                    self.blocks[block_id]["inputs"][input_name] = [1, menu_id]
            
            return None
        
        # === Field-based functions (set_rotation_style) ===
        if func_name in self.FIELD_FUNCTION_MAP:
            opcode, field_name, valid_values = self.FIELD_FUNCTION_MAP[func_name]
            
            # Create the block
            block_id = self._create_block(opcode=opcode, inputs={})
            
            # Get the style argument
            if node.args:
                style_value = self._extract_value(node.args[0])
                # Validate and set the field
                if isinstance(style_value, str):
                    self.blocks[block_id]["fields"][field_name] = [style_value, None]
            
            return None
        
        # === Broadcast functions (need special handling for broadcast IDs) ===
        if func_name == 'broadcast':
            if node.args:
                message_name = self._extract_value(node.args[0])
                if isinstance(message_name, str):
                    broadcast_id = self._get_or_create_broadcast(message_name)
                    block_id = self._create_block(opcode='event_broadcast', inputs={})
                    # BROADCAST_INPUT is a special format with broadcast ID
                    self.blocks[block_id]["inputs"]["BROADCAST_INPUT"] = [1, [11, message_name, broadcast_id]]
            return None
        
        if func_name == 'broadcast_and_wait':
            if node.args:
                message_name = self._extract_value(node.args[0])
                if isinstance(message_name, str):
                    broadcast_id = self._get_or_create_broadcast(message_name)
                    block_id = self._create_block(opcode='event_broadcastandwait', inputs={})
                    self.blocks[block_id]["inputs"]["BROADCAST_INPUT"] = [1, [11, message_name, broadcast_id]]
            return None
        
        # === Key pressed boolean reporter ===
        if func_name == 'key_pressed':
            block_id = self._create_block(opcode='sensing_keypressed', inputs={}, is_reporter=True)
            if node.args:
                key_value = self._extract_value(node.args[0])
                if isinstance(key_value, str):
                    # Map common key names
                    key_map = {
                        'space': 'space', 'up': 'up arrow', 'down': 'down arrow',
                        'left': 'left arrow', 'right': 'right arrow', 'any': 'any',
                    }
                    key_value = key_map.get(key_value, key_value)
                    menu_id = self._create_menu_block('sensing_keyoptions', 'KEY_OPTION', key_value, block_id)
                    self.blocks[block_id]["inputs"]["KEY_OPTION"] = [1, menu_id]
            return block_id
        
        # === Touching boolean reporter ===  
        if func_name == 'touching':
            block_id = self._create_block(opcode='sensing_touchingobject', inputs={}, is_reporter=True)
            if node.args:
                target_value = self._extract_value(node.args[0])
                if isinstance(target_value, str):
                    target_map = {'mouse': '_mouse_', 'edge': '_edge_'}
                    target_value = target_map.get(target_value.lower(), target_value)
                    menu_id = self._create_menu_block('sensing_touchingobjectmenu', 'TOUCHINGOBJECTMENU', target_value, block_id)
                    self.blocks[block_id]["inputs"]["TOUCHINGOBJECTMENU"] = [1, menu_id]
            return block_id
        
        # === Touching color boolean reporter ===
        if func_name == 'touching_color':
            block_id = self._create_block(opcode='sensing_touchingcolor', inputs={}, is_reporter=True)
            if node.args:
                color_value = self._extract_value(node.args[0])
                # Color is expected as a hex string or number
                self.blocks[block_id]["inputs"]["COLOR"] = [1, [9, str(color_value)]]
            return block_id
        
        # === Distance to reporter ===
        if func_name == 'distance_to':
            block_id = self._create_block(opcode='sensing_distanceto', inputs={}, is_reporter=True)
            if node.args:
                target_value = self._extract_value(node.args[0])
                if isinstance(target_value, str):
                    target_map = {'mouse': '_mouse_'}
                    target_value = target_map.get(target_value.lower(), target_value)
                    menu_id = self._create_menu_block('sensing_distancetomenu', 'DISTANCETOMENU', target_value, block_id)
                    self.blocks[block_id]["inputs"]["DISTANCETOMENU"] = [1, menu_id]
            return block_id
        
        # === Random number operator ===
        if func_name == 'pick_random' or func_name == 'random':
            block_id = self._create_block(opcode='operator_random', inputs={}, is_reporter=True)
            inputs = {}
            if len(node.args) >= 2:
                from_val = self._extract_value(node.args[0])
                to_val = self._extract_value(node.args[1])
                inputs.update(self._create_literal_input(from_val, 'FROM', block_id))
                inputs.update(self._create_literal_input(to_val, 'TO', block_id))
            elif len(node.args) == 1:
                # random(n) -> random(1, n)
                inputs.update(self._create_literal_input(1, 'FROM', block_id))
                to_val = self._extract_value(node.args[0])
                inputs.update(self._create_literal_input(to_val, 'TO', block_id))
            self.blocks[block_id]["inputs"] = inputs
            return block_id
        
        # === Math functions ===
        if func_name in ['abs', 'floor', 'ceiling', 'sqrt', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'ln', 'log', 'e_pow', 'ten_pow']:
            # Map Python function names to Scratch mathop values
            mathop_map = {
                'abs': 'abs', 'floor': 'floor', 'ceiling': 'ceiling', 
                'sqrt': 'sqrt', 'sin': 'sin', 'cos': 'cos', 'tan': 'tan',
                'asin': 'asin', 'acos': 'acos', 'atan': 'atan',
                'ln': 'ln', 'log': 'log', 'e_pow': 'e ^', 'ten_pow': '10 ^'
            }
            block_id = self._create_block(opcode='operator_mathop', inputs={}, is_reporter=True)
            self.blocks[block_id]["fields"]["OPERATOR"] = [mathop_map[func_name], None]
            if node.args:
                num_val = self._extract_value(node.args[0])
                inputs = self._create_literal_input(num_val, 'NUM', block_id)
                self.blocks[block_id]["inputs"] = inputs
            return block_id
        
        # === String operators ===
        if func_name == 'join':
            block_id = self._create_block(opcode='operator_join', inputs={}, is_reporter=True)
            inputs = {}
            if len(node.args) >= 2:
                str1 = self._extract_value(node.args[0])
                str2 = self._extract_value(node.args[1])
                inputs.update(self._create_literal_input(str1, 'STRING1', block_id))
                inputs.update(self._create_literal_input(str2, 'STRING2', block_id))
            self.blocks[block_id]["inputs"] = inputs
            return block_id
        
        if func_name == 'letter_of':
            block_id = self._create_block(opcode='operator_letter_of', inputs={}, is_reporter=True)
            inputs = {}
            if len(node.args) >= 2:
                letter_num = self._extract_value(node.args[0])
                string = self._extract_value(node.args[1])
                inputs.update(self._create_literal_input(letter_num, 'LETTER', block_id))
                inputs.update(self._create_literal_input(string, 'STRING', block_id))
            self.blocks[block_id]["inputs"] = inputs
            return block_id
        
        if func_name == 'length':
            block_id = self._create_block(opcode='operator_length', inputs={}, is_reporter=True)
            if node.args:
                string = self._extract_value(node.args[0])
                inputs = self._create_literal_input(string, 'STRING', block_id)
                self.blocks[block_id]["inputs"] = inputs
            return block_id
        
        if func_name == 'contains':
            block_id = self._create_block(opcode='operator_contains', inputs={}, is_reporter=True)
            inputs = {}
            if len(node.args) >= 2:
                str1 = self._extract_value(node.args[0])
                str2 = self._extract_value(node.args[1])
                inputs.update(self._create_literal_input(str1, 'STRING1', block_id))
                inputs.update(self._create_literal_input(str2, 'STRING2', block_id))
            self.blocks[block_id]["inputs"] = inputs
            return block_id
        
        if func_name == 'round':
            block_id = self._create_block(opcode='operator_round', inputs={}, is_reporter=True)
            if node.args:
                num = self._extract_value(node.args[0])
                inputs = self._create_literal_input(num, 'NUM', block_id)
                self.blocks[block_id]["inputs"] = inputs
            return block_id
        
        # === List operations ===
        # add_to_list(item, list_name) -> data_addtolist
        if func_name == 'add_to_list':
            if len(node.args) >= 2:
                item = self._extract_value(node.args[0])
                list_name = self._extract_value(node.args[1])
                if isinstance(list_name, str):
                    list_id = self._get_or_create_list(list_name)
                    block_id = self._create_block(opcode='data_addtolist', inputs={})
                    inputs = self._create_literal_input(item, 'ITEM', block_id)
                    self.blocks[block_id]["inputs"] = inputs
                    self.blocks[block_id]["fields"]["LIST"] = [list_name, list_id]
            return None
        
        # delete_of_list(index, list_name) -> data_deleteoflist
        if func_name == 'delete_of_list':
            if len(node.args) >= 2:
                index = self._extract_value(node.args[0])
                list_name = self._extract_value(node.args[1])
                if isinstance(list_name, str):
                    list_id = self._get_or_create_list(list_name)
                    block_id = self._create_block(opcode='data_deleteoflist', inputs={})
                    inputs = self._create_literal_input(index, 'INDEX', block_id)
                    self.blocks[block_id]["inputs"] = inputs
                    self.blocks[block_id]["fields"]["LIST"] = [list_name, list_id]
            return None
        
        # delete_all_of_list(list_name) -> data_deletealloflist
        if func_name == 'delete_all_of_list':
            if node.args:
                list_name = self._extract_value(node.args[0])
                if isinstance(list_name, str):
                    list_id = self._get_or_create_list(list_name)
                    block_id = self._create_block(opcode='data_deletealloflist', inputs={})
                    self.blocks[block_id]["fields"]["LIST"] = [list_name, list_id]
            return None
        
        # insert_at_list(index, item, list_name) -> data_insertatlist
        if func_name == 'insert_at_list':
            if len(node.args) >= 3:
                index = self._extract_value(node.args[0])
                item = self._extract_value(node.args[1])
                list_name = self._extract_value(node.args[2])
                if isinstance(list_name, str):
                    list_id = self._get_or_create_list(list_name)
                    block_id = self._create_block(opcode='data_insertatlist', inputs={})
                    inputs = {}
                    inputs.update(self._create_literal_input(item, 'ITEM', block_id))
                    inputs.update(self._create_literal_input(index, 'INDEX', block_id))
                    self.blocks[block_id]["inputs"] = inputs
                    self.blocks[block_id]["fields"]["LIST"] = [list_name, list_id]
            return None
        
        # replace_item_of_list(index, item, list_name) -> data_replaceitemoflist
        if func_name == 'replace_item_of_list':
            if len(node.args) >= 3:
                index = self._extract_value(node.args[0])
                item = self._extract_value(node.args[1])
                list_name = self._extract_value(node.args[2])
                if isinstance(list_name, str):
                    list_id = self._get_or_create_list(list_name)
                    block_id = self._create_block(opcode='data_replaceitemoflist', inputs={})
                    inputs = {}
                    inputs.update(self._create_literal_input(index, 'INDEX', block_id))
                    inputs.update(self._create_literal_input(item, 'ITEM', block_id))
                    self.blocks[block_id]["inputs"] = inputs
                    self.blocks[block_id]["fields"]["LIST"] = [list_name, list_id]
            return None
        
        # item_of_list(index, list_name) -> data_itemoflist (reporter)
        if func_name == 'item_of_list':
            if len(node.args) >= 2:
                index = self._extract_value(node.args[0])
                list_name = self._extract_value(node.args[1])
                if isinstance(list_name, str):
                    list_id = self._get_or_create_list(list_name)
                    block_id = self._create_block(opcode='data_itemoflist', inputs={}, is_reporter=True)
                    inputs = self._create_literal_input(index, 'INDEX', block_id)
                    self.blocks[block_id]["inputs"] = inputs
                    self.blocks[block_id]["fields"]["LIST"] = [list_name, list_id]
                    return block_id
            return None
        
        # item_num_of_list(item, list_name) -> data_itemnumoflist (reporter)
        if func_name == 'item_num_of_list':
            if len(node.args) >= 2:
                item = self._extract_value(node.args[0])
                list_name = self._extract_value(node.args[1])
                if isinstance(list_name, str):
                    list_id = self._get_or_create_list(list_name)
                    block_id = self._create_block(opcode='data_itemnumoflist', inputs={}, is_reporter=True)
                    inputs = self._create_literal_input(item, 'ITEM', block_id)
                    self.blocks[block_id]["inputs"] = inputs
                    self.blocks[block_id]["fields"]["LIST"] = [list_name, list_id]
                    return block_id
            return None
        
        # length_of_list(list_name) -> data_lengthoflist (reporter)
        if func_name == 'length_of_list':
            if node.args:
                list_name = self._extract_value(node.args[0])
                if isinstance(list_name, str):
                    list_id = self._get_or_create_list(list_name)
                    block_id = self._create_block(opcode='data_lengthoflist', inputs={}, is_reporter=True)
                    self.blocks[block_id]["fields"]["LIST"] = [list_name, list_id]
                    return block_id
            return None
        
        # list_contains(list_name, item) -> data_listcontainsitem (boolean reporter)
        if func_name == 'list_contains':
            if len(node.args) >= 2:
                list_name = self._extract_value(node.args[0])
                item = self._extract_value(node.args[1])
                if isinstance(list_name, str):
                    list_id = self._get_or_create_list(list_name)
                    block_id = self._create_block(opcode='data_listcontainsitem', inputs={}, is_reporter=True)
                    inputs = self._create_literal_input(item, 'ITEM', block_id)
                    self.blocks[block_id]["inputs"] = inputs
                    self.blocks[block_id]["fields"]["LIST"] = [list_name, list_id]
                    return block_id
            return None
        
        # show_list(list_name) -> data_showlist
        if func_name == 'show_list':
            if node.args:
                list_name = self._extract_value(node.args[0])
                if isinstance(list_name, str):
                    list_id = self._get_or_create_list(list_name)
                    block_id = self._create_block(opcode='data_showlist', inputs={})
                    self.blocks[block_id]["fields"]["LIST"] = [list_name, list_id]
            return None
        
        # hide_list(list_name) -> data_hidelist
        if func_name == 'hide_list':
            if node.args:
                list_name = self._extract_value(node.args[0])
                if isinstance(list_name, str):
                    list_id = self._get_or_create_list(list_name)
                    block_id = self._create_block(opcode='data_hidelist', inputs={})
                    self.blocks[block_id]["fields"]["LIST"] = [list_name, list_id]
            return None
        
        # show_variable(var_name) -> data_showvariable
        if func_name == 'show_variable':
            if node.args:
                var_name = self._extract_value(node.args[0])
                if isinstance(var_name, str):
                    var_id = self._get_or_create_variable(var_name)
                    block_id = self._create_block(opcode='data_showvariable', inputs={})
                    self.blocks[block_id]["fields"]["VARIABLE"] = [var_name, var_id]
            return None
        
        # hide_variable(var_name) -> data_hidevariable
        if func_name == 'hide_variable':
            if node.args:
                var_name = self._extract_value(node.args[0])
                if isinstance(var_name, str):
                    var_id = self._get_or_create_variable(var_name)
                    block_id = self._create_block(opcode='data_hidevariable', inputs={})
                    self.blocks[block_id]["fields"]["VARIABLE"] = [var_name, var_id]
            return None
        
        # === Color is touching color (sensing_coloristouchingcolor) ===
        if func_name == 'color_touching_color':
            block_id = self._create_block(opcode='sensing_coloristouchingcolor', inputs={}, is_reporter=True)
            if len(node.args) >= 2:
                color1 = self._extract_value(node.args[0])
                color2 = self._extract_value(node.args[1])
                self.blocks[block_id]["inputs"]["COLOR"] = [1, [9, str(color1)]]
                self.blocks[block_id]["inputs"]["COLOR2"] = [1, [9, str(color2)]]
            return block_id
        
        # === Sensing "of" block (get property of another sprite) ===
        if func_name == 'property_of':
            # property_of("x position", "Sprite1") -> sensing_of
            block_id = self._create_block(opcode='sensing_of', inputs={}, is_reporter=True)
            if len(node.args) >= 2:
                property_name = self._extract_value(node.args[0])
                object_name = self._extract_value(node.args[1])
                if isinstance(property_name, str):
                    # Map Python names to Scratch property names
                    property_map = {
                        'x position': 'x position', 'y position': 'y position',
                        'direction': 'direction', 'costume #': 'costume #',
                        'costume name': 'costume name', 'size': 'size',
                        'volume': 'volume', 'backdrop #': 'backdrop #',
                        'backdrop name': 'backdrop name'
                    }
                    scratch_prop = property_map.get(property_name, property_name)
                    self.blocks[block_id]["fields"]["PROPERTY"] = [scratch_prop, None]
                if isinstance(object_name, str):
                    menu_id = self._create_menu_block('sensing_of_object_menu', 'OBJECT', object_name, block_id)
                    self.blocks[block_id]["inputs"]["OBJECT"] = [1, menu_id]
            return block_id
        
        # === Wait until (control_wait_until) ===
        if func_name == 'wait_until':
            block_id = self._create_block(opcode='control_wait_until', inputs={})
            # The argument should be a condition (boolean expression)
            if node.args:
                # Process the condition
                condition_block_id = self._process_condition(node.args[0])
                if condition_block_id:
                    self.blocks[block_id]["inputs"]["CONDITION"] = [2, condition_block_id]
                    self.blocks[condition_block_id]["parent"] = block_id
            return None
        
        # === Custom block calls (My Blocks) ===
        if func_name in self.custom_blocks:
            call_args = [self._extract_value(arg) for arg in node.args]
            self._create_procedure_call(func_name, call_args)
            return None
        
        # === Check for argument references within custom blocks ===
        if hasattr(self, '_current_proc_args') and func_name in getattr(self, '_current_proc_args', {}):
            # This is a reference to a procedure argument
            arg_id = self._current_proc_args[func_name]
            block_id = self._generate_id()
            self.blocks[block_id] = {
                "opcode": "argument_reporter_string_number",
                "next": None,
                "parent": None,
                "inputs": {},
                "fields": {
                    "VALUE": [func_name, None]
                },
                "shadow": False,
                "topLevel": False,
            }
            return block_id
        
        return None

    def transpile(self, source_code: str) -> List[Dict[str, Any]]:
        """
        Transpile Python source code to Scratch targets (sprites).
        
        Args:
            source_code: Python source code string
            
        Returns:
            List of target dictionaries, each containing:
            - name: Sprite name
            - blocks: Dictionary of blocks
            - variables: Dictionary of variable definitions
            - lists: Dictionary of list definitions
            - broadcasts: Dictionary of broadcast definitions
        """
        # Reset all state
        self.blocks = {}
        self.current_parent_id = None
        self.previous_block_id = None
        self.hat_block_id = None
        self.variable_ids = {}
        self.variable_definitions = {}
        self.list_ids = {}
        self.list_definitions = {}
        self.broadcast_ids = {}
        self.custom_blocks = {}
        self._current_proc_args = {}
        self.sounds_used = set()
        self.targets = []
        self.current_sprite_name = None
        self.stage_blocks = {}
        self.stage_variables = {}
        
        # Parse the Python code into an AST
        tree = ast.parse(source_code)
        
        # Visit all nodes in the AST
        self.visit(tree)
        
        # If there are blocks outside of classes, create a default sprite
        if self.blocks:
            self.targets.insert(0, {
                'name': 'Sprite1',
                'blocks': self.blocks,
                'variables': self.variable_definitions,
                'lists': self.list_definitions,
                'broadcasts': self.broadcast_ids,
            })
        
        return self.targets


def create_project_json(targets: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a complete Scratch 3.0 project.json structure.
    
    Args:
        targets: List of target dictionaries from transpiler, each with:
                 - name: Sprite name (used to look up in sprite library)
                 - blocks: Dictionary of blocks
                 - variables: Dictionary of variable definitions
        
    Returns:
        Complete project.json dictionary
    """
    if targets is None:
        targets = []
    
    # Default backdrop - use embedded SVG (simple blue background)
    backdrop_hash = hashlib.md5(BACKDROP_SVG.encode()).hexdigest()
    backdrop_costume = {
        "name": "backdrop1",
        "dataFormat": "svg",
        "assetId": backdrop_hash,
        "md5ext": f"{backdrop_hash}.svg",
        "rotationCenterX": 240,
        "rotationCenterY": 180
    }
    
    # Stage target (required, always first)
    stage = {
        "isStage": True,
        "name": "Stage",
        "variables": {},
        "lists": {},
        "broadcasts": {},
        "blocks": {},
        "comments": {},
        "currentCostume": 0,
        "costumes": [backdrop_costume],
        "sounds": [],
        "volume": 100,
        "layerOrder": 0,
        "tempo": 60,
        "videoTransparency": 50,
        "videoState": "on",
        "textToSpeechLanguage": None
    }
    
    all_targets = [stage]
    
    # Create sprite targets from the transpiler output
    for i, target_data in enumerate(targets):
        sprite_name = target_data.get('name', f'Sprite{i+1}')
        
        # Try to get costumes/sounds from sprite library
        costumes = None
        sounds = None
        
        if SPRITE_LIBRARY_AVAILABLE:
            # Try exact match first, then fuzzy match
            actual_name = find_sprite_by_name(sprite_name, fuzzy=True)
            if actual_name:
                costumes = get_costume_data_for_project(actual_name)
                sounds = get_sound_data_for_project(actual_name)
        
        # Fall back to embedded Cat if sprite not in library
        if not costumes:
            cat_a_hash = hashlib.md5(CAT_COSTUME_A.encode()).hexdigest()
            cat_b_hash = hashlib.md5(CAT_COSTUME_B.encode()).hexdigest()
            costumes = [
                {
                    "name": "cat-a",
                    "bitmapResolution": 1,
                    "dataFormat": "svg",
                    "assetId": cat_a_hash,
                    "md5ext": f"{cat_a_hash}.svg",
                    "rotationCenterX": 48,
                    "rotationCenterY": 50
                },
                {
                    "name": "cat-b",
                    "bitmapResolution": 1,
                    "dataFormat": "svg",
                    "assetId": cat_b_hash,
                    "md5ext": f"{cat_b_hash}.svg",
                    "rotationCenterX": 46,
                    "rotationCenterY": 53
                }
            ]
        
        # Make sure sounds is a list (not None)
        if sounds is None:
            sounds = []
        
        # Add any sounds referenced in code that aren't already in the sprite's sounds
        sounds_used = target_data.get('sounds_used', set())
        existing_sound_names = {s.get('name', '').lower() for s in sounds}
        
        for sound_name in sounds_used:
            # Check if sound already exists (case-insensitive)
            if sound_name.lower() not in existing_sound_names:
                # Try to get from sound library
                if SPRITE_LIBRARY_AVAILABLE:
                    sound_data = get_library_sound_for_project(sound_name)
                    if sound_data:
                        sounds.append(sound_data)
                        existing_sound_names.add(sound_name.lower())
        
        sprite = {
            "isStage": False,
            "name": sprite_name,
            "variables": target_data.get('variables', {}),
            "lists": target_data.get('lists', {}),
            "broadcasts": target_data.get('broadcasts', {}),
            "blocks": target_data.get('blocks', {}),
            "comments": {},
            "currentCostume": 0,
            "costumes": costumes,
            "sounds": sounds,
            "volume": 100,
            "layerOrder": i + 1,
            "visible": True,
            "x": i * 100 - 100,  # Spread sprites out
            "y": 0,
            "size": 100,
            "direction": 90,
            "draggable": False,
            "rotationStyle": "all around"
        }
        all_targets.append(sprite)
    
    # Complete project structure
    project = {
        "targets": all_targets,
        "monitors": [],
        "extensions": [],
        "meta": {
            "semver": "3.0.0",
            "vm": "0.2.0",
            "agent": "Python-to-Scratch Transpiler"
        }
    }
    
    return project


def transpile_to_json(source_code: str, indent: int = 2) -> str:
    """
    Main entry point: Transpile Python code to Scratch project.json string.
    
    Args:
        source_code: Python source code to transpile
        indent: JSON indentation level (default: 2)
        
    Returns:
        JSON string of the complete Scratch project
    """
    transpiler = ScratchTranspiler()
    targets = transpiler.transpile(source_code)
    project = create_project_json(targets)
    return json.dumps(project, indent=indent)


# ============================================================================
# SB3 File Generation with Embedded Assets
# ============================================================================

# Embedded SVG costumes - used when CDN is unavailable
# These are simplified versions that display correctly in Scratch

EMBEDDED_COSTUMES = {
    # Cat costumes (orange cat)
    "cat-a": '''<svg xmlns="http://www.w3.org/2000/svg" width="96" height="100">
  <g fill="#FFAB19" stroke="#D89400" stroke-width="2">
    <ellipse cx="48" cy="60" rx="35" ry="28"/>
    <ellipse cx="48" cy="35" rx="28" ry="23"/>
    <polygon points="25,20 15,0 30,15"/>
    <polygon points="71,20 81,0 66,15"/>
  </g>
  <g fill="white">
    <ellipse cx="38" cy="32" rx="8" ry="10"/>
    <ellipse cx="58" cy="32" rx="8" ry="10"/>
    <ellipse cx="48" cy="55" rx="18" ry="12"/>
  </g>
  <g fill="black">
    <circle cx="40" cy="32" r="4"/>
    <circle cx="56" cy="32" r="4"/>
    <ellipse cx="48" cy="45" rx="3" ry="2"/>
  </g>
  <path d="M48,47 Q48,52 43,55" fill="none" stroke="black" stroke-width="1.5"/>
  <path d="M48,47 Q48,52 53,55" fill="none" stroke="black" stroke-width="1.5"/>
  <g stroke="#D89400" stroke-width="1.5" fill="none">
    <path d="M20,40 L5,35"/><path d="M20,45 L5,45"/><path d="M20,50 L5,55"/>
    <path d="M76,40 L91,35"/><path d="M76,45 L91,45"/><path d="M76,50 L91,55"/>
  </g>
</svg>''',

    "cat-b": '''<svg xmlns="http://www.w3.org/2000/svg" width="96" height="100">
  <g fill="#FFAB19" stroke="#D89400" stroke-width="2">
    <ellipse cx="48" cy="58" rx="32" ry="30"/>
    <ellipse cx="48" cy="32" rx="26" ry="22"/>
    <polygon points="28,18 20,0 32,14"/>
    <polygon points="68,18 76,0 64,14"/>
    <ellipse cx="22" cy="70" rx="10" ry="16" transform="rotate(-15 22 70)"/>
    <ellipse cx="74" cy="70" rx="10" ry="16" transform="rotate(15 74 70)"/>
  </g>
  <g fill="white">
    <ellipse cx="38" cy="30" rx="8" ry="10"/>
    <ellipse cx="58" cy="30" rx="8" ry="10"/>
    <ellipse cx="48" cy="52" rx="16" ry="11"/>
  </g>
  <g fill="black">
    <circle cx="40" cy="30" r="4"/>
    <circle cx="56" cy="30" r="4"/>
    <ellipse cx="48" cy="44" rx="3" ry="2"/>
  </g>
  <path d="M48,46 Q48,50 43,52" fill="none" stroke="black" stroke-width="1.5"/>
  <path d="M48,46 Q48,50 53,52" fill="none" stroke="black" stroke-width="1.5"/>
  <g stroke="#D89400" stroke-width="1.5" fill="none">
    <path d="M20,38 L5,33"/><path d="M20,43 L5,43"/><path d="M20,48 L5,53"/>
    <path d="M76,38 L91,33"/><path d="M76,43 L91,43"/><path d="M76,48 L91,53"/>
  </g>
</svg>''',

    # Dog costumes (brown dog)
    "dog-a": '''<svg xmlns="http://www.w3.org/2000/svg" width="80" height="90">
  <g fill="#A0522D" stroke="#8B4513" stroke-width="2">
    <ellipse cx="40" cy="55" rx="28" ry="25"/>
    <ellipse cx="40" cy="30" rx="22" ry="20"/>
    <ellipse cx="15" cy="25" rx="12" ry="18" transform="rotate(-20 15 25)"/>
    <ellipse cx="65" cy="25" rx="12" ry="18" transform="rotate(20 65 25)"/>
    <ellipse cx="40" cy="85" rx="8" ry="5"/>
  </g>
  <g fill="white">
    <ellipse cx="32" cy="28" rx="7" ry="9"/>
    <ellipse cx="48" cy="28" rx="7" ry="9"/>
    <ellipse cx="40" cy="48" rx="12" ry="10"/>
  </g>
  <g fill="black">
    <circle cx="34" cy="28" r="4"/>
    <circle cx="46" cy="28" r="4"/>
    <ellipse cx="40" cy="40" rx="5" ry="4"/>
  </g>
  <path d="M40,44 L40,50" fill="none" stroke="black" stroke-width="1.5"/>
  <ellipse cx="40" cy="52" rx="8" ry="4" fill="#FF9999" stroke="none"/>
  <path d="M32,56 Q40,62 48,56" fill="none" stroke="black" stroke-width="1.5"/>
</svg>''',

    "dog-b": '''<svg xmlns="http://www.w3.org/2000/svg" width="90" height="90">
  <g fill="#A0522D" stroke="#8B4513" stroke-width="2">
    <ellipse cx="45" cy="55" rx="30" ry="25"/>
    <ellipse cx="45" cy="30" rx="24" ry="20"/>
    <ellipse cx="18" cy="22" rx="14" ry="16" transform="rotate(-30 18 22)"/>
    <ellipse cx="72" cy="22" rx="14" ry="16" transform="rotate(30 72 22)"/>
    <ellipse cx="18" cy="65" rx="10" ry="15" transform="rotate(-10 18 65)"/>
    <ellipse cx="72" cy="65" rx="10" ry="15" transform="rotate(10 72 65)"/>
  </g>
  <g fill="white">
    <ellipse cx="36" cy="28" rx="7" ry="9"/>
    <ellipse cx="54" cy="28" rx="7" ry="9"/>
    <ellipse cx="45" cy="50" rx="14" ry="10"/>
  </g>
  <g fill="black">
    <circle cx="38" cy="28" r="4"/>
    <circle cx="52" cy="28" r="4"/>
    <ellipse cx="45" cy="42" rx="5" ry="4"/>
  </g>
  <path d="M45,46 L45,52" fill="none" stroke="black" stroke-width="1.5"/>
  <ellipse cx="45" cy="54" rx="10" ry="5" fill="#FF9999" stroke="none"/>
  <path d="M35,58 Q45,66 55,58" fill="none" stroke="black" stroke-width="1.5"/>
</svg>''',

    # Backdrop (white)
    "backdrop1": '''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360">
  <rect width="480" height="360" fill="white"/>
</svg>''',
}

# Keep old names for backward compatibility
CAT_COSTUME_A = EMBEDDED_COSTUMES["cat-a"]
CAT_COSTUME_B = EMBEDDED_COSTUMES["cat-b"]
BACKDROP_SVG = EMBEDDED_COSTUMES["backdrop1"]

# Map sprite library asset IDs to embedded costume names
# When CDN fails, we use these fallbacks
ASSET_ID_TO_EMBEDDED = {
    # Cat
    "b7853f557e4426412e64bb3da6531a99": "cat-a",
    "e6ddc55a6ddd9cc9d84c0fa5ce29e6b8": "cat-b",
    # Dog  
    "96b7d7f5c6a644b5b2317d62d5232827": "dog-a",
    "fb35e307ffae1b0f6a0348e5b5f94ab1": "dog-b",
    # Backdrop
    "cd21514d0531fdffb22204e0ec5ed84a": "backdrop1",
}

def save_sb3(json_content: str, filename: str = "output.sb3", source_sb3: str = None) -> None:
    """
    Save the project.json as a .sb3 file (ZIP archive) with embedded assets.
    
    Downloads and includes official Scratch assets from the sprite library.
    Falls back to embedded SVGs if library is unavailable.
    
    Args:
        json_content: The project.json string
        filename: Output filename (default: "output.sb3")
        source_sb3: Optional source .sb3 file to copy assets from (for round-trip)
    """
    # Parse project.json to find all required assets
    project_data = json.loads(json_content)
    required_assets = set()
    
    for target in project_data.get("targets", []):
        for costume in target.get("costumes", []):
            md5ext = costume.get("md5ext")
            if md5ext:
                required_assets.add(md5ext)
        for sound in target.get("sounds", []):
            md5ext = sound.get("md5ext")
            if md5ext:
                required_assets.add(md5ext)
    
    # Load assets from source .sb3 if provided
    source_assets = {}
    if source_sb3:
        try:
            with zipfile.ZipFile(source_sb3, 'r') as src_zf:
                for name in src_zf.namelist():
                    if name != 'project.json':
                        source_assets[name] = src_zf.read(name)
        except Exception as e:
            print(f"  Warning: Could not read source assets: {e}")
    
    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add the project.json
        zf.writestr("project.json", json_content)
        
        # Add each required asset
        for md5ext in required_assets:
            asset_id, data_format = md5ext.rsplit('.', 1)
            
            # First, try to get from source .sb3 (for round-trip)
            if md5ext in source_assets:
                zf.writestr(md5ext, source_assets[md5ext])
                continue
            
            # Try to get from sprite library cache
            asset_data = None
            if SPRITE_LIBRARY_AVAILABLE:
                asset_data = get_cached_asset(asset_id, data_format)
            
            if asset_data:
                zf.writestr(md5ext, asset_data)
            else:
                # Fallback: check if we have an embedded version
                embedded_name = ASSET_ID_TO_EMBEDDED.get(asset_id)
                if embedded_name and embedded_name in EMBEDDED_COSTUMES:
                    zf.writestr(md5ext, EMBEDDED_COSTUMES[embedded_name])
                else:
                    # Check for hash-based embedded assets (backward compat)
                    cat_a_hash = hashlib.md5(CAT_COSTUME_A.encode()).hexdigest()
                    cat_b_hash = hashlib.md5(CAT_COSTUME_B.encode()).hexdigest()
                    backdrop_hash = hashlib.md5(BACKDROP_SVG.encode()).hexdigest()
                    
                    if asset_id == cat_a_hash:
                        zf.writestr(md5ext, CAT_COSTUME_A)
                    elif asset_id == cat_b_hash:
                        zf.writestr(md5ext, CAT_COSTUME_B)
                    elif asset_id == backdrop_hash:
                        zf.writestr(md5ext, BACKDROP_SVG)
                    elif data_format != "wav":  # Don't warn about missing sounds
                        print(f"  Warning: Asset not found: {md5ext}")
        
    print(f"Saved: {filename}")


def get_asset_ids() -> dict:
    """
    Get the MD5 hashes for the embedded assets.
    These must match the assetId values in project.json.
    """
    import hashlib
    return {
        'cat_a': hashlib.md5(CAT_COSTUME_A.encode()).hexdigest(),
        'cat_b': hashlib.md5(CAT_COSTUME_B.encode()).hexdigest(),
        'backdrop': hashlib.md5(BACKDROP_SVG.encode()).hexdigest(),
    }


# ============================================================================
# Reverse Transpiler: Scratch (.sb3) to Python
# ============================================================================

class ScratchToPython:
    """
    Reverse transpiler that converts Scratch .sb3 files to Python code.
    
    Usage:
        converter = ScratchToPython()
        python_code = converter.convert("project.sb3")
        print(python_code)
    """
    
    # Map Scratch opcodes to Python function calls
    # Format: opcode -> (function_name, [input_names], [field_names])
    OPCODE_MAP = {
        # Motion
        'motion_movesteps': ('move', ['STEPS']),
        'motion_turnright': ('turn_right', ['DEGREES']),
        'motion_turnleft': ('turn_left', ['DEGREES']),
        'motion_goto': ('go_to', ['TO']),
        'motion_gotoxy': ('go_to_xy', ['X', 'Y']),
        'motion_glideto': ('glide_to', ['SECS', 'TO']),
        'motion_glidesecstoxy': ('glide_to_xy', ['SECS', 'X', 'Y']),
        'motion_pointindirection': ('point_in_direction', ['DIRECTION']),
        'motion_pointtowards': ('point_towards', ['TOWARDS']),
        'motion_changexby': ('change_x', ['DX']),
        'motion_setx': ('set_x', ['X']),
        'motion_changeyby': ('change_y', ['DY']),
        'motion_sety': ('set_y', ['Y']),
        'motion_ifonedgebounce': ('if_on_edge_bounce', []),
        'motion_setrotationstyle': ('set_rotation_style', [], ['STYLE']),
        'motion_xposition': ('x_position', []),
        'motion_yposition': ('y_position', []),
        'motion_direction': ('direction', []),
        
        # Looks
        'looks_sayforsecs': ('say_for_secs', ['MESSAGE', 'SECS']),
        'looks_say': ('say', ['MESSAGE']),
        'looks_thinkforsecs': ('think_for_secs', ['MESSAGE', 'SECS']),
        'looks_think': ('think', ['MESSAGE']),
        'looks_switchcostumeto': ('switch_costume', ['COSTUME']),
        'looks_nextcostume': ('next_costume', []),
        'looks_switchbackdropto': ('switch_backdrop', ['BACKDROP']),
        'looks_nextbackdrop': ('next_backdrop', []),
        'looks_changesizeby': ('change_size', ['CHANGE']),
        'looks_setsizeto': ('set_size', ['SIZE']),
        'looks_changeeffectby': ('change_effect', [], ['EFFECT'], ['CHANGE']),
        'looks_seteffectto': ('set_effect', [], ['EFFECT'], ['VALUE']),
        'looks_cleargraphiceffects': ('clear_effects', []),
        'looks_show': ('show', []),
        'looks_hide': ('hide', []),
        'looks_gotofrontback': ('go_to_layer', [], ['FRONT_BACK']),
        'looks_goforwardbackwardlayers': ('change_layer', [], ['FORWARD_BACKWARD'], ['NUM']),
        'looks_costumenumbername': ('costume_number', []),  # or costume_name based on field
        'looks_backdropnumbername': ('backdrop_number', []),  # or backdrop_name based on field
        'looks_size': ('size', []),
        
        # Sound
        'sound_playuntildone': ('play_sound_until_done', ['SOUND_MENU']),
        'sound_play': ('play_sound', ['SOUND_MENU']),
        'sound_stopallsounds': ('stop_all_sounds', []),
        'sound_changeeffectby': ('change_sound_effect', [], ['EFFECT'], ['VALUE']),
        'sound_seteffectto': ('set_sound_effect', [], ['EFFECT'], ['VALUE']),
        'sound_cleareffects': ('clear_sound_effects', []),
        'sound_changevolumeby': ('change_volume', ['VOLUME']),
        'sound_setvolumeto': ('set_volume', ['VOLUME']),
        'sound_volume': ('volume', []),
        
        # Events
        'event_whenflagclicked': ('when_flag_clicked', []),
        'event_whenkeypressed': ('when_key_', [], ['KEY_OPTION']),
        'event_whenthisspriteclicked': ('when_clicked', []),
        'event_whenbackdropswitchesto': ('when_backdrop_', [], ['BACKDROP']),
        'event_whengreaterthan': ('when_greater_than', [], ['WHENGREATERTHANMENU'], ['VALUE']),
        'event_whenbroadcastreceived': ('when_broadcast_', [], ['BROADCAST_OPTION']),
        'event_broadcast': ('broadcast', ['BROADCAST_INPUT']),
        'event_broadcastandwait': ('broadcast_and_wait', ['BROADCAST_INPUT']),
        
        # Control
        'control_wait': ('wait', ['DURATION']),
        'control_repeat': ('for i in range', ['TIMES']),  # Special handling
        'control_forever': ('while True', []),  # Special handling
        'control_if': ('if', ['CONDITION']),  # Special handling
        'control_if_else': ('if_else', ['CONDITION']),  # Special handling
        'control_wait_until': ('wait_until', ['CONDITION']),
        'control_repeat_until': ('while', ['CONDITION']),  # Special handling
        'control_stop': ('stop', [], ['STOP_OPTION']),
        'control_start_as_clone': ('when_i_start_as_clone', []),
        'control_create_clone_of': ('create_clone', ['CLONE_OPTION']),
        'control_delete_this_clone': ('delete_this_clone', []),
        
        # Sensing
        'sensing_touchingobject': ('touching', ['TOUCHINGOBJECTMENU']),
        'sensing_touchingcolor': ('touching_color', ['COLOR']),
        'sensing_coloristouchingcolor': ('color_touching_color', ['COLOR', 'COLOR2']),
        'sensing_distanceto': ('distance_to', ['DISTANCETOMENU']),
        'sensing_askandwait': ('ask', ['QUESTION']),
        'sensing_answer': ('answer', []),
        'sensing_keypressed': ('key_pressed', ['KEY_OPTION']),
        'sensing_mousedown': ('mouse_down', []),
        'sensing_mousex': ('mouse_x', []),
        'sensing_mousey': ('mouse_y', []),
        'sensing_setdragmode': ('set_drag_mode', [], ['DRAG_MODE']),
        'sensing_loudness': ('loudness', []),
        'sensing_timer': ('timer', []),
        'sensing_resettimer': ('reset_timer', []),
        'sensing_of': ('property_of', [], ['PROPERTY'], ['OBJECT']),
        'sensing_current': ('current_', [], ['CURRENTMENU']),
        'sensing_dayssince2000': ('days_since_2000', []),
        'sensing_username': ('username', []),
        
        # Operators
        'operator_add': ('+', ['NUM1', 'NUM2']),  # Special: infix
        'operator_subtract': ('-', ['NUM1', 'NUM2']),  # Special: infix
        'operator_multiply': ('*', ['NUM1', 'NUM2']),  # Special: infix
        'operator_divide': ('/', ['NUM1', 'NUM2']),  # Special: infix
        'operator_random': ('pick_random', ['FROM', 'TO']),
        'operator_gt': ('>', ['OPERAND1', 'OPERAND2']),  # Special: infix
        'operator_lt': ('<', ['OPERAND1', 'OPERAND2']),  # Special: infix
        'operator_equals': ('==', ['OPERAND1', 'OPERAND2']),  # Special: infix
        'operator_and': ('and', ['OPERAND1', 'OPERAND2']),  # Special: infix
        'operator_or': ('or', ['OPERAND1', 'OPERAND2']),  # Special: infix
        'operator_not': ('not', ['OPERAND']),  # Special: prefix
        'operator_join': ('join', ['STRING1', 'STRING2']),
        'operator_letter_of': ('letter_of', ['LETTER', 'STRING']),
        'operator_length': ('length', ['STRING']),
        'operator_contains': ('contains', ['STRING1', 'STRING2']),
        'operator_mod': ('%', ['NUM1', 'NUM2']),  # Special: infix
        'operator_round': ('round', ['NUM']),
        'operator_mathop': ('mathop', ['NUM']),  # Special: check OPERATOR field
        
        # Variables
        'data_setvariableto': ('=', ['VALUE']),  # Special: assignment
        'data_changevariableby': ('+=', ['VALUE']),  # Special: augmented assignment
        'data_showvariable': ('show_variable', [], ['VARIABLE']),
        'data_hidevariable': ('hide_variable', [], ['VARIABLE']),
        'data_variable': ('variable', []),  # Reporter
        
        # Lists
        'data_addtolist': ('add_to_list', ['ITEM'], ['LIST']),
        'data_deleteoflist': ('delete_of_list', ['INDEX'], ['LIST']),
        'data_deletealloflist': ('delete_all_of_list', [], ['LIST']),
        'data_insertatlist': ('insert_at_list', ['INDEX', 'ITEM'], ['LIST']),
        'data_replaceitemoflist': ('replace_item_of_list', ['INDEX', 'ITEM'], ['LIST']),
        'data_itemoflist': ('item_of_list', ['INDEX'], ['LIST']),
        'data_itemnumoflist': ('item_num_of_list', ['ITEM'], ['LIST']),
        'data_lengthoflist': ('length_of_list', [], ['LIST']),
        'data_listcontainsitem': ('list_contains', ['ITEM'], ['LIST']),
        'data_showlist': ('show_list', [], ['LIST']),
        'data_hidelist': ('hide_list', [], ['LIST']),
        
        # Custom blocks
        'procedures_definition': ('define_', []),  # Special handling
        'procedures_call': ('call_', []),  # Special handling
    }
    
    # Math operation mapping
    MATHOP_MAP = {
        'abs': 'abs',
        'floor': 'floor',
        'ceiling': 'ceiling',
        'sqrt': 'sqrt',
        'sin': 'sin',
        'cos': 'cos',
        'tan': 'tan',
        'asin': 'asin',
        'acos': 'acos',
        'atan': 'atan',
        'ln': 'ln',
        'log': 'log',
        'e ^': 'exp',
        'e^': 'exp',
        '10 ^': 'pow10',
        '10^': 'pow10',
    }
    
    # Infix operators
    INFIX_OPS = {'+', '-', '*', '/', '%', '>', '<', '==', 'and', 'or'}
    
    def __init__(self):
        self.blocks = {}
        self.variables = {}
        self.lists = {}
        self.custom_blocks = {}  # proccode -> (name, args)
        self.indent = 0
        
    def convert(self, sb3_path: str) -> str:
        """
        Convert an .sb3 file to Python code.
        
        Args:
            sb3_path: Path to the .sb3 file
            
        Returns:
            Python source code string
        """
        # Load project.json from the .sb3 file
        with zipfile.ZipFile(sb3_path, 'r') as zf:
            project_json = json.loads(zf.read('project.json'))
        
        return self.convert_project(project_json)
    
    def convert_project(self, project: dict) -> str:
        """Convert a project.json dict to Python code."""
        output_lines = []
        output_lines.append('"""')
        output_lines.append('Scratch project converted to Python')
        output_lines.append('"""')
        output_lines.append('')
        output_lines.append('from scratch.dsl import *')
        output_lines.append('')
        
        # Extract global variables and lists from Stage
        stage = next((t for t in project.get('targets', []) if t.get('isStage')), None)
        if stage:
            stage_vars = stage.get('variables', {})
            stage_lists = stage.get('lists', {})
            
            if stage_vars:
                output_lines.append('# Global variables')
                for var_id, var_data in stage_vars.items():
                    if isinstance(var_data, list) and len(var_data) >= 2:
                        var_name = self._to_identifier(var_data[0])
                        var_value = var_data[1]
                        output_lines.append(f'{var_name} = {self._format_value(var_value)}')
                output_lines.append('')
            
            if stage_lists:
                output_lines.append('# Global lists')
                for list_id, list_data in stage_lists.items():
                    if isinstance(list_data, list) and len(list_data) >= 2:
                        list_name = self._to_identifier(list_data[0])
                        list_value = list_data[1] if len(list_data) > 1 else []
                        output_lines.append(f'{list_name} = {list_value}')
                output_lines.append('')
        
        # Process each sprite (skip the stage for now)
        for target in project.get('targets', []):
            if target.get('isStage'):
                continue
            
            sprite_code = self._convert_sprite(target)
            if sprite_code:
                output_lines.append(sprite_code)
                output_lines.append('')
        
        return '\n'.join(output_lines)
    
    def _convert_sprite(self, target: dict) -> str:
        """Convert a single sprite to a Python class."""
        sprite_name = target.get('name', 'Sprite')
        # Clean up the name to be a valid Python identifier
        class_name = self._to_identifier(sprite_name)
        
        self.blocks = target.get('blocks', {})
        self.variables = target.get('variables', {})
        self.lists = target.get('lists', {})
        self.custom_blocks = {}
        
        # First pass: collect custom block definitions
        self._collect_custom_blocks()
        
        lines = []
        lines.append(f'class {class_name}:')
        
        # Add variable declarations with initial values
        if self.variables:
            for var_id, var_data in self.variables.items():
                if isinstance(var_data, list) and len(var_data) >= 2:
                    var_name = self._to_identifier(var_data[0])
                    var_value = var_data[1]
                    lines.append(f'    {var_name} = {self._format_value(var_value)}')
        
        # Add list declarations
        if self.lists:
            for list_id, list_data in self.lists.items():
                if isinstance(list_data, list) and len(list_data) >= 2:
                    list_name = self._to_identifier(list_data[0])
                    list_value = list_data[1] if len(list_data) > 1 else []
                    lines.append(f'    {list_name} = {list_value}')
        
        if self.variables or self.lists:
            lines.append('')
        
        # Find all top-level hat blocks (scripts)
        hat_blocks = self._find_hat_blocks()
        
        if not hat_blocks:
            lines.append('    pass')
            return '\n'.join(lines)
        
        for hat_id in hat_blocks:
            method_code = self._convert_script(hat_id)
            if method_code:
                lines.append(method_code)
        
        return '\n'.join(lines)
    
    def _collect_custom_blocks(self):
        """Collect custom block definitions (procedures)."""
        for block_id, block in self.blocks.items():
            if block.get('opcode') == 'procedures_definition':
                # Get the prototype
                custom_block_input = block.get('inputs', {}).get('custom_block', [])
                if len(custom_block_input) >= 2:
                    proto_id = custom_block_input[1]
                    proto = self.blocks.get(proto_id, {})
                    mutation = proto.get('mutation', {})
                    proccode = mutation.get('proccode', '')
                    
                    # Parse proccode to get name and args
                    # Format: "block_name %s %s" or "block_name %b %n"
                    parts = proccode.split()
                    if parts:
                        name = parts[0]
                        # Count arguments
                        arg_names_json = mutation.get('argumentnames', '[]')
                        try:
                            arg_names = json.loads(arg_names_json)
                        except:
                            arg_names = []
                        
                        self.custom_blocks[proccode] = (name, arg_names, block_id)
    
    def _find_hat_blocks(self) -> List[str]:
        """Find all top-level hat blocks (event handlers)."""
        hat_opcodes = {
            'event_whenflagclicked',
            'event_whenkeypressed',
            'event_whenthisspriteclicked',
            'event_whenbackdropswitchesto',
            'event_whengreaterthan',
            'event_whenbroadcastreceived',
            'control_start_as_clone',
            'procedures_definition',
        }
        
        hats = []
        for block_id, block in self.blocks.items():
            if isinstance(block, dict) and block.get('topLevel') and block.get('opcode') in hat_opcodes:
                hats.append(block_id)
        
        return hats
    
    def _convert_script(self, hat_id: str) -> str:
        """Convert a script (starting from a hat block) to a Python method."""
        hat = self.blocks.get(hat_id, {})
        opcode = hat.get('opcode', '')
        
        # Determine method name based on hat type
        method_name = self._get_method_name(hat)
        if not method_name:
            return ''
        
        # Get method parameters (for custom blocks)
        params = self._get_method_params(hat)
        
        lines = []
        self.indent = 1
        
        # Method signature
        if params:
            lines.append(f'    def {method_name}(self, {", ".join(params)}):')
        else:
            lines.append(f'    def {method_name}(self):')
        
        # Convert the body
        next_id = hat.get('next')
        if next_id:
            body_lines = self._convert_block_chain(next_id)
            if body_lines:
                lines.extend(body_lines)
            else:
                lines.append('        pass')
        else:
            lines.append('        pass')
        
        return '\n'.join(lines)
    
    def _get_method_name(self, hat: dict) -> str:
        """Get the Python method name for a hat block."""
        opcode = hat.get('opcode', '')
        fields = hat.get('fields', {})
        
        if opcode == 'event_whenflagclicked':
            return 'when_flag_clicked'
        elif opcode == 'event_whenkeypressed':
            key = self._get_field_value(fields, 'KEY_OPTION')
            # Convert key name to method name
            # "up arrow" -> "up", "space" -> "space", "a" -> "a"
            key_name = key.lower().replace(' arrow', '').replace(' ', '_')
            if key_name == 'any':
                return 'when_key_any'
            return f'when_key_{key_name}'
        elif opcode == 'event_whenthisspriteclicked':
            return 'when_clicked'
        elif opcode == 'event_whenbroadcastreceived':
            broadcast = self._get_field_value(fields, 'BROADCAST_OPTION')
            return f'when_broadcast_{self._to_identifier(broadcast)}'
        elif opcode == 'control_start_as_clone':
            return 'when_i_start_as_clone'
        elif opcode == 'procedures_definition':
            # Get custom block name
            custom_block_input = hat.get('inputs', {}).get('custom_block', [])
            if len(custom_block_input) >= 2:
                proto_id = custom_block_input[1]
                proto = self.blocks.get(proto_id, {})
                mutation = proto.get('mutation', {})
                proccode = mutation.get('proccode', '')
                parts = proccode.split()
                if parts:
                    return f'define_{parts[0]}'
            return 'define_custom'
        
        return ''
    
    def _get_method_params(self, hat: dict) -> List[str]:
        """Get method parameters for custom block definitions."""
        opcode = hat.get('opcode', '')
        
        if opcode == 'procedures_definition':
            custom_block_input = hat.get('inputs', {}).get('custom_block', [])
            if len(custom_block_input) >= 2:
                proto_id = custom_block_input[1]
                proto = self.blocks.get(proto_id, {})
                mutation = proto.get('mutation', {})
                arg_names_json = mutation.get('argumentnames', '[]')
                try:
                    return json.loads(arg_names_json)
                except:
                    return []
        return []
    
    def _convert_block_chain(self, block_id: str, indent: int = 2) -> List[str]:
        """Convert a chain of blocks to Python code."""
        lines = []
        current_id = block_id
        
        while current_id:
            block = self.blocks.get(current_id, {})
            if not isinstance(block, dict):
                break
            
            block_lines = self._convert_block(block, indent)
            lines.extend(block_lines)
            
            current_id = block.get('next')
        
        return lines
    
    def _convert_block(self, block: dict, indent: int = 2) -> List[str]:
        """Convert a single block to Python code."""
        opcode = block.get('opcode', '')
        inputs = block.get('inputs', {})
        fields = block.get('fields', {})
        
        prefix = '    ' * indent
        lines = []
        
        # Handle control structures specially
        if opcode == 'control_forever':
            lines.append(f'{prefix}while True:')
            substack = self._get_substack(inputs, 'SUBSTACK')
            if substack:
                lines.extend(self._convert_block_chain(substack, indent + 1))
            else:
                lines.append(f'{prefix}    pass')
            return lines
        
        elif opcode == 'control_repeat':
            times = self._get_input_value(inputs, 'TIMES')
            lines.append(f'{prefix}for i in range({times}):')
            substack = self._get_substack(inputs, 'SUBSTACK')
            if substack:
                lines.extend(self._convert_block_chain(substack, indent + 1))
            else:
                lines.append(f'{prefix}    pass')
            return lines
        
        elif opcode == 'control_repeat_until':
            condition = self._get_condition(inputs, 'CONDITION')
            # "repeat until X" = "while not X"
            lines.append(f'{prefix}while not ({condition}):')
            substack = self._get_substack(inputs, 'SUBSTACK')
            if substack:
                lines.extend(self._convert_block_chain(substack, indent + 1))
            else:
                lines.append(f'{prefix}    pass')
            return lines
        
        elif opcode == 'control_if':
            condition = self._get_condition(inputs, 'CONDITION')
            lines.append(f'{prefix}if {condition}:')
            substack = self._get_substack(inputs, 'SUBSTACK')
            if substack:
                lines.extend(self._convert_block_chain(substack, indent + 1))
            else:
                lines.append(f'{prefix}    pass')
            return lines
        
        elif opcode == 'control_if_else':
            condition = self._get_condition(inputs, 'CONDITION')
            lines.append(f'{prefix}if {condition}:')
            substack = self._get_substack(inputs, 'SUBSTACK')
            if substack:
                lines.extend(self._convert_block_chain(substack, indent + 1))
            else:
                lines.append(f'{prefix}    pass')
            lines.append(f'{prefix}else:')
            substack2 = self._get_substack(inputs, 'SUBSTACK2')
            if substack2:
                lines.extend(self._convert_block_chain(substack2, indent + 1))
            else:
                lines.append(f'{prefix}    pass')
            return lines
        
        elif opcode == 'data_setvariableto':
            var_name = self._to_identifier(self._get_field_value(fields, 'VARIABLE'))
            value = self._get_input_value(inputs, 'VALUE')
            lines.append(f'{prefix}{var_name} = {value}')
            return lines
        
        elif opcode == 'data_changevariableby':
            var_name = self._to_identifier(self._get_field_value(fields, 'VARIABLE'))
            value = self._get_input_value(inputs, 'VALUE')
            lines.append(f'{prefix}{var_name} += {value}')
            return lines
        
        # List operations - need specific handlers for correct argument order
        elif opcode == 'data_addtolist':
            item = self._get_input_value(inputs, 'ITEM')
            list_name = self._get_field_value(fields, 'LIST')
            lines.append(f'{prefix}add_to_list({item}, "{list_name}")')
            return lines
        
        elif opcode == 'data_deleteoflist':
            index = self._get_input_value(inputs, 'INDEX')
            list_name = self._get_field_value(fields, 'LIST')
            lines.append(f'{prefix}delete_of_list({index}, "{list_name}")')
            return lines
        
        elif opcode == 'data_deletealloflist':
            list_name = self._get_field_value(fields, 'LIST')
            lines.append(f'{prefix}delete_all_of_list("{list_name}")')
            return lines
        
        elif opcode == 'data_insertatlist':
            index = self._get_input_value(inputs, 'INDEX')
            item = self._get_input_value(inputs, 'ITEM')
            list_name = self._get_field_value(fields, 'LIST')
            lines.append(f'{prefix}insert_at_list({index}, {item}, "{list_name}")')
            return lines
        
        elif opcode == 'data_replaceitemoflist':
            index = self._get_input_value(inputs, 'INDEX')
            item = self._get_input_value(inputs, 'ITEM')
            list_name = self._get_field_value(fields, 'LIST')
            lines.append(f'{prefix}replace_item_of_list({index}, {item}, "{list_name}")')
            return lines
        
        elif opcode == 'data_showlist':
            list_name = self._get_field_value(fields, 'LIST')
            lines.append(f'{prefix}show_list("{list_name}")')
            return lines
        
        elif opcode == 'data_hidelist':
            list_name = self._get_field_value(fields, 'LIST')
            lines.append(f'{prefix}hide_list("{list_name}")')
            return lines
        
        elif opcode == 'procedures_call':
            # Custom block call
            mutation = block.get('mutation', {})
            proccode = mutation.get('proccode', '')
            
            # Get function name from proccode
            parts = proccode.split()
            if parts:
                func_name = parts[0]
                # Get argument values
                arg_ids_json = mutation.get('argumentids', '[]')
                try:
                    arg_ids = json.loads(arg_ids_json)
                except:
                    arg_ids = []
                
                args = []
                for arg_id in arg_ids:
                    if arg_id in inputs:
                        args.append(self._get_input_value(inputs, arg_id))
                
                lines.append(f'{prefix}{func_name}({", ".join(args)})')
            return lines
        
        # General case: lookup in OPCODE_MAP
        if opcode in self.OPCODE_MAP:
            mapping = self.OPCODE_MAP[opcode]
            func_name = mapping[0]
            input_names = mapping[1] if len(mapping) > 1 else []
            field_names = mapping[2] if len(mapping) > 2 else []
            field_input_names = mapping[3] if len(mapping) > 3 else []
            
            # Handle special cases
            if opcode == 'looks_changeeffectby' or opcode == 'looks_seteffectto':
                effect = self._get_field_value(fields, 'EFFECT')
                value = self._get_input_value(inputs, 'CHANGE' if 'CHANGE' in inputs else 'VALUE')
                lines.append(f'{prefix}{func_name}("{effect.lower()}", {value})')
                return lines
            
            elif opcode == 'sound_changeeffectby' or opcode == 'sound_seteffectto':
                effect = self._get_field_value(fields, 'EFFECT')
                value = self._get_input_value(inputs, 'VALUE')
                lines.append(f'{prefix}{func_name}("{effect.lower()}", {value})')
                return lines
            
            elif opcode == 'looks_gotofrontback':
                direction = self._get_field_value(fields, 'FRONT_BACK')
                lines.append(f'{prefix}{func_name}("{direction}")')
                return lines
            
            elif opcode == 'looks_goforwardbackwardlayers':
                direction = self._get_field_value(fields, 'FORWARD_BACKWARD')
                num = self._get_input_value(inputs, 'NUM')
                lines.append(f'{prefix}{func_name}("{direction.lower()}", {num})')
                return lines
            
            elif opcode == 'control_stop':
                option = self._get_field_value(fields, 'STOP_OPTION')
                lines.append(f'{prefix}stop("{option}")')
                return lines
            
            elif opcode == 'sensing_of':
                prop = self._get_field_value(fields, 'PROPERTY')
                obj = self._get_input_value(inputs, 'OBJECT')
                lines.append(f'{prefix}property_of("{prop}", {obj})')
                return lines
            
            elif opcode == 'control_wait_until':
                condition = self._get_condition(inputs, 'CONDITION')
                lines.append(f'{prefix}wait_until({condition})')
                return lines
            
            # Default: build function call
            args = []
            
            # Add field-based arguments first (like effect name)
            for field_name in field_names:
                val = self._get_field_value(fields, field_name)
                if val:
                    args.append(f'"{val}"')
            
            # Add input-based arguments
            for input_name in input_names:
                val = self._get_input_value(inputs, input_name)
                args.append(str(val))
            
            # Add any field-input combo args
            for input_name in field_input_names:
                val = self._get_input_value(inputs, input_name)
                args.append(str(val))
            
            lines.append(f'{prefix}{func_name}({", ".join(args)})')
            return lines
        
        # Unknown opcode - add as comment
        lines.append(f'{prefix}# Unknown: {opcode}')
        return lines
    
    def _get_input_value(self, inputs: dict, name: str) -> str:
        """Get the Python representation of an input value."""
        if name not in inputs:
            return '0'
        
        input_data = inputs[name]
        
        # Input format: [shadow_type, value_or_block_id, ...]
        if not isinstance(input_data, list) or len(input_data) < 2:
            return '0'
        
        value = input_data[1]
        
        # If value is a string, it's a block ID
        if isinstance(value, str):
            return self._convert_reporter(value)
        
        # If value is a list, it's a literal value
        if isinstance(value, list):
            return self._convert_literal(value)
        
        return str(value)
    
    def _convert_literal(self, literal: list) -> str:
        """Convert a Scratch literal value to Python."""
        if len(literal) < 2:
            return '0'
        
        type_code = literal[0]
        value = literal[1]
        
        # Type codes:
        # 4, 5, 6, 7, 8 = number
        # 10 = string
        # 11 = broadcast
        # 12 = variable
        # 13 = list
        
        if type_code in (4, 5, 6, 7, 8):
            # Number - try to convert
            try:
                if '.' in str(value):
                    return str(float(value))
                return str(int(value))
            except:
                return str(value)
        elif type_code == 9:
            # Color - stored as #RRGGBB string
            return f'"{value}"'
        elif type_code == 10:
            # String
            return f'"{value}"'
        elif type_code == 11:
            # Broadcast
            return f'"{value}"'
        elif type_code == 12:
            # Variable reference - sanitize to valid Python identifier
            return self._to_identifier(str(value))
        elif type_code == 13:
            # List reference - sanitize to valid Python identifier
            return self._to_identifier(str(value))
        
        return str(value)
    
    def _convert_reporter(self, block_id: str) -> str:
        """Convert a reporter block to a Python expression."""
        block = self.blocks.get(block_id, {})
        if not isinstance(block, dict):
            return '0'
        
        opcode = block.get('opcode', '')
        inputs = block.get('inputs', {})
        fields = block.get('fields', {})
        
        # Handle variables
        if opcode == 'data_variable':
            var_name = self._get_field_value(fields, 'VARIABLE')
            return self._to_identifier(var_name)
        
        # Handle argument reporters (custom block parameters)
        if opcode == 'argument_reporter_string_number':
            arg_name = self._get_field_value(fields, 'VALUE')
            return self._to_identifier(arg_name)
        
        # Handle infix operators
        if opcode == 'operator_add':
            left = self._get_input_value(inputs, 'NUM1')
            right = self._get_input_value(inputs, 'NUM2')
            return f'({left} + {right})'
        elif opcode == 'operator_subtract':
            left = self._get_input_value(inputs, 'NUM1')
            right = self._get_input_value(inputs, 'NUM2')
            return f'({left} - {right})'
        elif opcode == 'operator_multiply':
            left = self._get_input_value(inputs, 'NUM1')
            right = self._get_input_value(inputs, 'NUM2')
            return f'({left} * {right})'
        elif opcode == 'operator_divide':
            left = self._get_input_value(inputs, 'NUM1')
            right = self._get_input_value(inputs, 'NUM2')
            return f'({left} / {right})'
        elif opcode == 'operator_mod':
            left = self._get_input_value(inputs, 'NUM1')
            right = self._get_input_value(inputs, 'NUM2')
            return f'({left} % {right})'
        elif opcode == 'operator_gt':
            left = self._get_input_value(inputs, 'OPERAND1')
            right = self._get_input_value(inputs, 'OPERAND2')
            return f'{left} > {right}'
        elif opcode == 'operator_lt':
            left = self._get_input_value(inputs, 'OPERAND1')
            right = self._get_input_value(inputs, 'OPERAND2')
            return f'{left} < {right}'
        elif opcode == 'operator_equals':
            left = self._get_input_value(inputs, 'OPERAND1')
            right = self._get_input_value(inputs, 'OPERAND2')
            return f'{left} == {right}'
        elif opcode == 'operator_and':
            left = self._get_input_value(inputs, 'OPERAND1')
            right = self._get_input_value(inputs, 'OPERAND2')
            return f'({left} and {right})'
        elif opcode == 'operator_or':
            left = self._get_input_value(inputs, 'OPERAND1')
            right = self._get_input_value(inputs, 'OPERAND2')
            return f'({left} or {right})'
        elif opcode == 'operator_not':
            operand = self._get_input_value(inputs, 'OPERAND')
            return f'not {operand}'
        
        # Handle random
        elif opcode == 'operator_random':
            from_val = self._get_input_value(inputs, 'FROM')
            to_val = self._get_input_value(inputs, 'TO')
            return f'pick_random({from_val}, {to_val})'
        
        # Handle math operations
        elif opcode == 'operator_mathop':
            operator = self._get_field_value(fields, 'OPERATOR')
            num = self._get_input_value(inputs, 'NUM')
            func = self.MATHOP_MAP.get(operator, operator)
            return f'{func}({num})'
        
        # Handle round
        elif opcode == 'operator_round':
            num = self._get_input_value(inputs, 'NUM')
            return f'round({num})'
        
        # Handle string operations
        elif opcode == 'operator_join':
            str1 = self._get_input_value(inputs, 'STRING1')
            str2 = self._get_input_value(inputs, 'STRING2')
            return f'join({str1}, {str2})'
        elif opcode == 'operator_letter_of':
            letter = self._get_input_value(inputs, 'LETTER')
            string = self._get_input_value(inputs, 'STRING')
            return f'letter_of({letter}, {string})'
        elif opcode == 'operator_length':
            string = self._get_input_value(inputs, 'STRING')
            return f'length({string})'
        elif opcode == 'operator_contains':
            str1 = self._get_input_value(inputs, 'STRING1')
            str2 = self._get_input_value(inputs, 'STRING2')
            return f'contains({str1}, {str2})'
        
        # Sensing reporters
        elif opcode == 'sensing_touchingobject':
            obj = self._get_input_value(inputs, 'TOUCHINGOBJECTMENU')
            return f'touching({obj})'
        elif opcode == 'sensing_touchingcolor':
            color = self._get_input_value(inputs, 'COLOR')
            return f'touching_color({color})'
        elif opcode == 'sensing_coloristouchingcolor':
            color1 = self._get_input_value(inputs, 'COLOR')
            color2 = self._get_input_value(inputs, 'COLOR2')
            return f'color_touching_color({color1}, {color2})'
        elif opcode == 'sensing_keypressed':
            key = self._get_input_value(inputs, 'KEY_OPTION')
            return f'key_pressed({key})'
        elif opcode == 'sensing_mousedown':
            return 'mouse_down()'
        elif opcode == 'sensing_mousex':
            return 'mouse_x()'
        elif opcode == 'sensing_mousey':
            return 'mouse_y()'
        elif opcode == 'sensing_distanceto':
            obj = self._get_input_value(inputs, 'DISTANCETOMENU')
            return f'distance_to({obj})'
        elif opcode == 'sensing_answer':
            return 'answer()'
        elif opcode == 'sensing_loudness':
            return 'loudness()'
        elif opcode == 'sensing_timer':
            return 'timer()'
        elif opcode == 'sensing_dayssince2000':
            return 'days_since_2000()'
        elif opcode == 'sensing_username':
            return 'username()'
        elif opcode == 'sensing_current':
            menu = self._get_field_value(fields, 'CURRENTMENU')
            func_map = {
                'YEAR': 'current_year',
                'MONTH': 'current_month',
                'DATE': 'current_date',
                'DAYOFWEEK': 'current_day',
                'HOUR': 'current_hour',
                'MINUTE': 'current_minute',
                'SECOND': 'current_second',
            }
            return f'{func_map.get(menu, "current_year")}()'
        elif opcode == 'sensing_of':
            prop = self._get_field_value(fields, 'PROPERTY')
            obj = self._get_input_value(inputs, 'OBJECT')
            return f'property_of("{prop}", {obj})'
        
        # Motion reporters
        elif opcode == 'motion_xposition':
            return 'x_position()'
        elif opcode == 'motion_yposition':
            return 'y_position()'
        elif opcode == 'motion_direction':
            return 'direction()'
        
        # Looks reporters
        elif opcode == 'looks_costumenumbername':
            field = self._get_field_value(fields, 'NUMBER_NAME')
            if field == 'name':
                return 'costume_name()'
            return 'costume_number()'
        elif opcode == 'looks_backdropnumbername':
            field = self._get_field_value(fields, 'NUMBER_NAME')
            if field == 'name':
                return 'backdrop_name()'
            return 'backdrop_number()'
        elif opcode == 'looks_size':
            return 'size()'
        
        # Sound reporters
        elif opcode == 'sound_volume':
            return 'volume()'
        
        # List reporters
        elif opcode == 'data_itemoflist':
            index = self._get_input_value(inputs, 'INDEX')
            list_name = self._get_field_value(fields, 'LIST')
            return f'item_of_list({index}, "{list_name}")'
        elif opcode == 'data_lengthoflist':
            list_name = self._get_field_value(fields, 'LIST')
            return f'length_of_list("{list_name}")'
        elif opcode == 'data_itemnumoflist':
            item = self._get_input_value(inputs, 'ITEM')
            list_name = self._get_field_value(fields, 'LIST')
            return f'item_num_of_list({item}, "{list_name}")'
        elif opcode == 'data_listcontainsitem':
            list_name = self._get_field_value(fields, 'LIST')
            item = self._get_input_value(inputs, 'ITEM')
            return f'list_contains("{list_name}", {item})'
        
        # Menu blocks (for motion targets, etc.)
        elif opcode in ('motion_goto_menu', 'motion_glideto_menu', 'motion_pointtowards_menu'):
            target = self._get_field_value(fields, 'TO') or self._get_field_value(fields, 'TOWARDS')
            if target == '_random_':
                return '"random"'
            elif target == '_mouse_':
                return '"mouse"'
            return f'"{target}"'
        
        elif opcode == 'sensing_touchingobjectmenu':
            obj = self._get_field_value(fields, 'TOUCHINGOBJECTMENU')
            if obj == '_mouse_':
                return '"mouse"'
            elif obj == '_edge_':
                return '"edge"'
            return f'"{obj}"'
        
        elif opcode == 'sensing_distancetomenu':
            obj = self._get_field_value(fields, 'DISTANCETOMENU')
            if obj == '_mouse_':
                return '"mouse"'
            return f'"{obj}"'
        
        elif opcode == 'sensing_keyoptions':
            key = self._get_field_value(fields, 'KEY_OPTION')
            return f'"{key}"'
        
        elif opcode == 'sound_sounds_menu':
            sound = self._get_field_value(fields, 'SOUND_MENU')
            return f'"{sound}"'
        
        elif opcode == 'looks_costume':
            costume = self._get_field_value(fields, 'COSTUME')
            return f'"{costume}"'
        
        elif opcode == 'looks_backdrops':
            backdrop = self._get_field_value(fields, 'BACKDROP')
            return f'"{backdrop}"'
        
        elif opcode == 'control_create_clone_of_menu':
            clone_opt = self._get_field_value(fields, 'CLONE_OPTION')
            if clone_opt == '_myself_':
                return '"myself"'
            return f'"{clone_opt}"'
        
        elif opcode == 'sensing_of_object_menu':
            obj = self._get_field_value(fields, 'OBJECT')
            return f'"{obj}"'
        
        # Unknown reporter
        return f'/* {opcode} */'
    
    def _get_condition(self, inputs: dict, name: str) -> str:
        """Get a condition expression from inputs."""
        if name not in inputs:
            return 'True'
        
        input_data = inputs[name]
        if not isinstance(input_data, list) or len(input_data) < 2:
            return 'True'
        
        value = input_data[1]
        
        if isinstance(value, str):
            return self._convert_reporter(value)
        
        return 'True'
    
    def _get_substack(self, inputs: dict, name: str) -> Optional[str]:
        """Get the first block ID of a substack."""
        if name not in inputs:
            return None
        
        input_data = inputs[name]
        if not isinstance(input_data, list) or len(input_data) < 2:
            return None
        
        value = input_data[1]
        if isinstance(value, str):
            return value
        
        return None
    
    def _get_field_value(self, fields: dict, name: str) -> str:
        """Get a field value."""
        if name not in fields:
            return ''
        
        field = fields[name]
        if isinstance(field, list) and len(field) > 0:
            return str(field[0])
        return ''
    
    def _to_identifier(self, name: str) -> str:
        """Convert a name to a valid Python identifier."""
        # Replace spaces and special chars with underscores
        result = ''
        for char in name:
            if char.isalnum():
                result += char
            else:
                result += '_'
        
        # Ensure it doesn't start with a digit
        if result and result[0].isdigit():
            result = '_' + result
        
        return result or 'Sprite'
    
    def _format_value(self, value) -> str:
        """Format a value for Python code, handling numeric strings."""
        if isinstance(value, bool):
            return str(value)
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Try to parse as number
            try:
                # Try int first
                int_val = int(value)
                return str(int_val)
            except ValueError:
                try:
                    # Try float
                    float_val = float(value)
                    return str(float_val)
                except ValueError:
                    # It's a real string
                    return f'"{value}"'
        else:
            return repr(value)


def sb3_to_python(sb3_path: str) -> str:
    """
    Convert an .sb3 file to Python code.
    
    Args:
        sb3_path: Path to the .sb3 file
        
    Returns:
        Python source code string
    """
    converter = ScratchToPython()
    return converter.convert(sb3_path)


def convert_sb3_to_py(sb3_path: str, output_path: str = None) -> str:
    """
    Convert an .sb3 file to a Python file.
    
    Args:
        sb3_path: Path to the .sb3 file
        output_path: Path for output .py file (default: same name as input)
        
    Returns:
        Path to the output file
    """
    if output_path is None:
        output_path = sb3_path.rsplit('.', 1)[0] + '.py'
    
    python_code = sb3_to_python(sb3_path)
    
    with open(output_path, 'w') as f:
        f.write(python_code)
    
    print(f"Converted: {sb3_path} -> {output_path}")
    return output_path


def roundtrip_sb3(sb3_path: str, output_path: str = None, py_path: str = None) -> str:
    """
    Round-trip an .sb3 file: convert to Python and back, preserving all assets.
    
    This is a true 1:1 conversion - the code is converted to Python and back,
    while sprites, backdrops, and sounds are copied directly from the source.
    
    Args:
        sb3_path: Path to the source .sb3 file
        output_path: Path for output .sb3 file (default: <name>_roundtrip.sb3)
        py_path: Optional path to save intermediate Python file
        
    Returns:
        Path to the output .sb3 file
    """
    if output_path is None:
        base = sb3_path.rsplit('.', 1)[0]
        output_path = f"{base}_roundtrip.sb3"
    
    # Step 1: Convert .sb3 to Python
    python_code = sb3_to_python(sb3_path)
    
    # Optionally save intermediate Python
    if py_path:
        with open(py_path, 'w') as f:
            f.write(python_code)
        print(f"  Intermediate: {py_path}")
    
    # Step 2: Convert Python back to project.json
    json_str = transpile_to_json(python_code)
    
    # Step 3: Parse and merge with original project to preserve asset metadata
    # Load original project.json to get costume/backdrop/sound definitions
    with zipfile.ZipFile(sb3_path, 'r') as zf:
        original_project = json.loads(zf.read('project.json').decode('utf-8'))
    
    new_project = json.loads(json_str)
    
    # Create a map of sprite names to their original target data
    original_targets = {t['name']: t for t in original_project.get('targets', [])}
    
    # Merge costume, backdrop, and sound data from original
    for target in new_project.get('targets', []):
        name = target.get('name', '')
        
        # Find matching original target
        # For Stage, match by name
        # For sprites, the Python class name might have been sanitized
        original = original_targets.get(name)
        
        if not original:
            # Try to find by similar name (Stage, or sprite name variations)
            if target.get('isStage'):
                original = next((t for t in original_project['targets'] if t.get('isStage')), None)
            else:
                # Try matching by index for sprites (non-stage targets)
                new_sprites = [t for t in new_project['targets'] if not t.get('isStage')]
                old_sprites = [t for t in original_project['targets'] if not t.get('isStage')]
                try:
                    idx = new_sprites.index(target)
                    if idx < len(old_sprites):
                        original = old_sprites[idx]
                except (ValueError, IndexError):
                    pass
        
        if original:
            # Copy costumes with all metadata
            target['costumes'] = original.get('costumes', [])
            target['sounds'] = original.get('sounds', [])
            target['currentCostume'] = original.get('currentCostume', 0)
            
            # Copy sprite position, size, direction, visibility
            if not target.get('isStage'):
                target['x'] = original.get('x', 0)
                target['y'] = original.get('y', 0)
                target['size'] = original.get('size', 100)
                target['direction'] = original.get('direction', 90)
                target['visible'] = original.get('visible', True)
                target['rotationStyle'] = original.get('rotationStyle', 'all around')
                target['draggable'] = original.get('draggable', False)
    
    # Copy stage-level data
    stage = next((t for t in new_project['targets'] if t.get('isStage')), None)
    original_stage = next((t for t in original_project['targets'] if t.get('isStage')), None)
    if stage and original_stage:
        stage['costumes'] = original_stage.get('costumes', [])
        stage['sounds'] = original_stage.get('sounds', [])
        stage['currentCostume'] = original_stage.get('currentCostume', 0)
        stage['tempo'] = original_stage.get('tempo', 60)
        stage['videoTransparency'] = original_stage.get('videoTransparency', 50)
        stage['videoState'] = original_stage.get('videoState', 'off')
        stage['textToSpeechLanguage'] = original_stage.get('textToSpeechLanguage', None)
    
    # Copy project metadata
    new_project['meta'] = original_project.get('meta', new_project.get('meta', {}))
    
    # Step 4: Save with assets from original file
    json_str = json.dumps(new_project)
    save_sb3(json_str, output_path, source_sb3=sb3_path)
    
    print(f"Round-trip: {sb3_path} -> {output_path}")
    return output_path


# ============================================================================
# Example Usage and Testing
# ============================================================================

if __name__ == "__main__":
    # Example: Comprehensive demo with all supported features!
    example_code = '''
class Cat:
    def when_flag_clicked(self):
        # Control - wait
        wait(1)
        say("Hello! I'm the cat!")
        
        # Variables
        score = 0
        
        # Forever loop with sensing
        while True:
            # Boolean conditions
            if key_pressed("space"):
                change_y(10)
            if touching("edge"):
                set_y(0)
            if mouse_down():
                go_to_xy(mouse_x(), mouse_y())
    
    def when_key_space(self):
        # Play sound and broadcast
        play_sound("Meow")
        broadcast("jumped")
    
    def when_broadcast_game_over(self):
        # Math operators
        final_score = score + random(1, 10)
        say_for_secs(join("Final: ", final_score), 2)
        stop("all")

class Dog:
    def when_flag_clicked(self):
        say("Woof!")
        
        # List operations
        delete_all_of_list("inventory")
        add_to_list("bone", "inventory")
        add_to_list("ball", "inventory")
        
        # Repeat loop
        for i in range(3):
            move(50)
            wait(0.5)
            turn_right(120)
        
        # Conditional with multiple conditions
        if touching("Cat") and not key_pressed("escape"):
            say("Found the cat!")
            broadcast("game_over")
    
    def when_i_start_as_clone(self):
        show()
        glide_to_xy(2, random(-200, 200), random(-150, 150))
        wait(1)
        delete_this_clone()
    
    def when_clicked(self):
        create_clone("myself")
'''

    # Also test backward-compatible function-based approach
    simple_example = '''
def when_flag_clicked():
    say("This still works!")
    move(10)
    switch_costume("cat-a")
'''
    
    print("=" * 60)
    print("Python to Scratch 3.0 Transpiler - Full Feature Demo")
    print("=" * 60)
    print("\nInput Python code:")
    print("-" * 40)
    print(example_code)
    print("-" * 40)
    
    # Transpile to JSON
    result = transpile_to_json(example_code)
    
    print("\nOutput project.json (truncated):")
    print("-" * 40)
    print(result[:2000] + "\n... [truncated]" if len(result) > 2000 else result)
    print("-" * 40)
    
    # Save as .sb3 file
    save_sb3(result, "full_demo_output.sb3")
    
    # Show target info
    print("\n\nGenerated Targets:")
    print("-" * 40)
    transpiler = ScratchTranspiler()
    targets = transpiler.transpile(example_code)
    
    for target in targets:
        print(f"\nSprite: {target['name']}")
        print(f"  Blocks: {len(target['blocks'])} blocks")
        print(f"  Variables: {len(target.get('variables', {}))} variables")
        print(f"  Lists: {len(target.get('lists', {}))} lists")
        
        # Show block chain for first script
        blocks = target['blocks']
        hat_blocks = []
        for block_id, block_data in blocks.items():
            if block_data.get('topLevel') and not block_data.get('shadow', False):
                hat_blocks.append((block_id, block_data))
        
        for hat_id, hat_data in hat_blocks[:2]:  # Show first 2 scripts
            chain = [blocks[hat_id]['opcode']]
            current_id = hat_id
            count = 0
            while blocks[current_id].get('next') and count < 5:
                current_id = blocks[current_id]['next']
                chain.append(blocks[current_id]['opcode'])
                count += 1
            suffix = "..." if count >= 5 else ""
            print(f"  Script: {' -> '.join(chain)}{suffix}")
    
    # Test simple function-based approach still works
    print("\n\nBackward Compatibility Test (function-based):")
    print("-" * 40)
    simple_targets = ScratchTranspiler().transpile(simple_example)
    for target in simple_targets:
        print(f"Sprite: {target['name']} - {len(target['blocks'])} blocks")
    save_sb3(transpile_to_json(simple_example), "simple_output.sb3")
    
    print("\n✓ All .sb3 files saved successfully!")
    print("\nSupported features:")
    print("  - Motion: move, turn, glide, go_to, point, position reporters")
    print("  - Looks: say, think, costumes, effects, show/hide, layers")
    print("  - Sound: play, stop, volume, effects")
    print("  - Events: flag clicked, key pressed, clicked, broadcasts")
    print("  - Control: wait, repeat, forever, if/else, clones, stop")
    print("  - Sensing: touching, key_pressed, mouse, distance, ask, timer")
    print("  - Operators: math (+,-,*,/,%), compare, boolean, random, strings")
    print("  - Variables: set, read in expressions")
    print("  - Lists: add, delete, insert, replace, item, contains, length")

