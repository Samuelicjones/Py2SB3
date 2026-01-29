"""
Scratch Transpiler - Bidirectional Python to Scratch 3.0 transpiler.

This package provides tools to:
- Convert Python code to Scratch 3.0 (.sb3) projects
- Convert Scratch 3.0 projects back to Python code
- Round-trip conversion preserving all assets

Quick Start:
    from scratch import create_scratch_file
    
    class Cat:
        def when_flag_clicked(self):
            say("Hello!")
            move(10)
    
    create_scratch_file()  # Creates .sb3 from this file

Or manually:
    from scratch import transpile_to_json, save_sb3

    code = '''
    class Cat:
        def when_flag_clicked(self):
            say("Hello!")
            move(10)
    '''
    
    json_str = transpile_to_json(code)
    save_sb3(json_str, "my_project.sb3")

For IDE support when writing Scratch code:
    from scratch.dsl import *

Convert existing Scratch projects:
    from scratch import convert_sb3_to_py, roundtrip_sb3
    
    # Convert .sb3 to Python
    convert_sb3_to_py("project.sb3", "project.py")
    
    # Round-trip (preserves sprites/sounds)
    roundtrip_sb3("input.sb3", "output.sb3")
"""

import inspect
import os
from pathlib import Path

from .transpiler import (
    # Main transpiler class
    ScratchTranspiler,
    
    # Reverse transpiler class
    ScratchToPython,
    
    # Core functions
    transpile_to_json,
    save_sb3,
    sb3_to_python,
    convert_sb3_to_py,
    roundtrip_sb3,
)

# Library functions
from .library import (
    get_sprite_data,
    get_costume_data_for_project,
    get_sound_data_for_project,
    find_sprite_by_name,
    list_sprites,
    list_sounds,
    get_library_sound_for_project,
    find_sound_by_name,
    download_sprite_assets,
)

__version__ = "1.0.0"
__author__ = "Scratch Transpiler"


def create_scratch_file(output: str = None):
    """
    Compile the current Python file to a Scratch .sb3 file.
    
    This function automatically detects the file it's called from,
    reads the source code, transpiles it, and saves the .sb3 file.
    
    Supports:
        - Custom sprites with @sprite decorator
        - Custom costumes from PNG/SVG files
        - Custom sounds from WAV/MP3 files
        - Custom backdrops via configure_stage()
    
    Args:
        output: Output .sb3 filename (default: same name as Python file)
    
    Example:
        from scratch import create_scratch_file
        from scratch.dsl import *
        
        class Cat:
            def when_flag_clicked(self):
                say("Hello!")
        
        create_scratch_file()  # Creates <filename>.sb3
        create_scratch_file("my_game.sb3")  # Custom output name
    """
    # Get the caller's frame to find the source file
    frame = inspect.currentframe()
    try:
        caller_frame = frame.f_back
        caller_file = caller_frame.f_globals.get('__file__')
        
        if caller_file is None:
            raise RuntimeError("Cannot determine source file. Use transpile_to_json() and save_sb3() instead.")
        
        caller_path = Path(caller_file).resolve()
        base_path = str(caller_path.parent)
        
        # Default output name: same as input but .sb3
        if output is None:
            output = str(caller_path.with_suffix('.sb3'))
        
        # Read the source code
        with open(caller_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Transpile and save (pass base_path for resolving relative asset paths)
        json_str, custom_assets = transpile_to_json(code, base_path=base_path)
        save_sb3(json_str, output, custom_assets=custom_assets)
        
    finally:
        del frame


__all__ = [
    # Classes
    'ScratchTranspiler',
    'ScratchToPython',
    
    # Core functions
    'transpile_to_json',
    'save_sb3',
    'create_scratch_file',
    'sb3_to_python',
    'convert_sb3_to_py',
    'roundtrip_sb3',
    
    # Library functions
    'get_sprite_data',
    'get_costume_data_for_project',
    'get_sound_data_for_project',
    'find_sprite_by_name',
    'list_sprites',
    'list_sounds',
    'get_library_sound_for_project',
    'find_sound_by_name',
    'download_sprite_assets',
    
    # Version
    '__version__',
]
