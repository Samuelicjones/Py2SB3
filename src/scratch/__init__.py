"""
Scratch Transpiler - Bidirectional Python to Scratch 3.0 transpiler.

This package provides tools to:
- Convert Python code to Scratch 3.0 (.sb3) projects
- Convert Scratch 3.0 projects back to Python code
- Round-trip conversion preserving all assets

Quick Start:
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

__all__ = [
    # Classes
    'ScratchTranspiler',
    'ScratchToPython',
    
    # Core functions
    'transpile_to_json',
    'save_sb3',
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
