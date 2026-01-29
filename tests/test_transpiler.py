"""
Tests for the Scratch Transpiler package.

Run with: pytest tests/
"""

import pytest
import json
import tempfile
import os


class TestTranspiler:
    """Tests for Python to Scratch transpilation."""
    
    def test_import(self):
        """Test that the package can be imported."""
        from scratch import transpile_to_json, save_sb3
        assert transpile_to_json is not None
        assert save_sb3 is not None
    
    def test_simple_sprite(self):
        """Test transpiling a simple sprite."""
        from scratch import transpile_to_json
        
        code = '''
class Cat:
    def when_flag_clicked(self):
        say("Hello!")
'''
        result = transpile_to_json(code)
        project = json.loads(result)
        
        # Check project structure
        assert 'targets' in project
        assert len(project['targets']) >= 2  # Stage + Cat
        
        # Find Cat sprite
        cat = None
        for target in project['targets']:
            if target.get('name') == 'Cat':
                cat = target
                break
        
        assert cat is not None
        assert 'blocks' in cat
        assert len(cat['blocks']) > 0
    
    def test_motion_blocks(self):
        """Test motion block transpilation."""
        from scratch import transpile_to_json
        
        code = '''
class Cat:
    def when_flag_clicked(self):
        move(10)
        turn_right(15)
        turn_left(15)
        go_to_xy(100, 50)
'''
        result = transpile_to_json(code)
        project = json.loads(result)
        
        cat = next(t for t in project['targets'] if t.get('name') == 'Cat')
        blocks = cat['blocks']
        
        # Check for motion opcodes
        opcodes = [b.get('opcode') for b in blocks.values() if isinstance(b, dict)]
        assert 'motion_movesteps' in opcodes
        assert 'motion_turnright' in opcodes
        assert 'motion_turnleft' in opcodes
        assert 'motion_gotoxy' in opcodes
    
    def test_control_blocks(self):
        """Test control block transpilation."""
        from scratch import transpile_to_json
        
        code = '''
class Cat:
    def when_flag_clicked(self):
        wait(1)
        for i in range(10):
            move(10)
'''
        result = transpile_to_json(code)
        project = json.loads(result)
        
        cat = next(t for t in project['targets'] if t.get('name') == 'Cat')
        blocks = cat['blocks']
        
        opcodes = [b.get('opcode') for b in blocks.values() if isinstance(b, dict)]
        assert 'control_wait' in opcodes
        assert 'control_repeat' in opcodes
    
    def test_forever_loop(self):
        """Test forever loop (while True) transpilation."""
        from scratch import transpile_to_json
        
        code = '''
class Cat:
    def when_flag_clicked(self):
        while True:
            move(1)
'''
        result = transpile_to_json(code)
        project = json.loads(result)
        
        cat = next(t for t in project['targets'] if t.get('name') == 'Cat')
        blocks = cat['blocks']
        
        opcodes = [b.get('opcode') for b in blocks.values() if isinstance(b, dict)]
        assert 'control_forever' in opcodes
    
    def test_if_else(self):
        """Test if/else transpilation."""
        from scratch import transpile_to_json
        
        code = '''
class Cat:
    def when_flag_clicked(self):
        if touching("edge"):
            turn_right(180)
        else:
            move(10)
'''
        result = transpile_to_json(code)
        project = json.loads(result)
        
        cat = next(t for t in project['targets'] if t.get('name') == 'Cat')
        blocks = cat['blocks']
        
        opcodes = [b.get('opcode') for b in blocks.values() if isinstance(b, dict)]
        assert 'control_if_else' in opcodes
        assert 'sensing_touchingobject' in opcodes
    
    def test_variables(self):
        """Test variable creation and usage."""
        from scratch import transpile_to_json
        
        code = '''
class Cat:
    def when_flag_clicked(self):
        score = 0
        score += 10
'''
        result = transpile_to_json(code)
        project = json.loads(result)
        
        cat = next(t for t in project['targets'] if t.get('name') == 'Cat')
        
        assert 'variables' in cat
        # Variable should be created
        assert len(cat['variables']) > 0
    
    def test_key_events(self):
        """Test key press event handlers."""
        from scratch import transpile_to_json
        
        code = '''
class Cat:
    def when_key_space(self):
        say("Jump!")
    
    def when_key_up(self):
        change_y(10)
'''
        result = transpile_to_json(code)
        project = json.loads(result)
        
        cat = next(t for t in project['targets'] if t.get('name') == 'Cat')
        blocks = cat['blocks']
        
        opcodes = [b.get('opcode') for b in blocks.values() if isinstance(b, dict)]
        assert opcodes.count('event_whenkeypressed') == 2
    
    def test_multiple_sprites(self):
        """Test multiple sprite classes."""
        from scratch import transpile_to_json
        
        code = '''
class Cat:
    def when_flag_clicked(self):
        say("I am Cat")

class Dog1:
    def when_flag_clicked(self):
        say("I am Dog")
'''
        result = transpile_to_json(code)
        project = json.loads(result)
        
        names = [t.get('name') for t in project['targets']]
        assert 'Cat' in names
        assert 'Dog1' in names


class TestReverseTranspiler:
    """Tests for Scratch to Python transpilation."""
    
    def test_roundtrip_simple(self):
        """Test that code can be transpiled and reverse-transpiled."""
        from scratch import transpile_to_json, ScratchToPython
        import zipfile
        import io
        
        code = '''
class Cat:
    def when_flag_clicked(self):
        say("Hello!")
        move(10)
'''
        # Python -> JSON
        json_str = transpile_to_json(code)
        project = json.loads(json_str)
        
        # JSON -> Python
        converter = ScratchToPython()
        python_code = converter.convert_project(project)
        
        assert 'class Cat' in python_code
        assert 'when_flag_clicked' in python_code
        assert 'say(' in python_code
        assert 'move(' in python_code


class TestDSL:
    """Tests for the DSL stubs."""
    
    def test_dsl_import(self):
        """Test that DSL can be imported."""
        from scratch.dsl import move, say, turn_right, wait
        
        # These are stubs, they should exist but do nothing
        assert move is not None
        assert say is not None
        assert turn_right is not None
        assert wait is not None
    
    def test_dsl_all_exports(self):
        """Test that __all__ exports are valid."""
        from scratch import dsl
        
        for name in dsl.__all__:
            assert hasattr(dsl, name), f"Missing export: {name}"


class TestLibrary:
    """Tests for the sprite/sound library."""
    
    def test_library_import(self):
        """Test that library can be imported."""
        from scratch.library import (
            SPRITE_LIBRARY, SOUNDS_LIBRARY,
            list_sprites, list_sounds
        )
        
        assert isinstance(SPRITE_LIBRARY, dict)
        assert isinstance(SOUNDS_LIBRARY, dict)
    
    def test_list_sprites(self):
        """Test listing sprites."""
        from scratch import list_sprites
        
        sprites = list_sprites()
        assert isinstance(sprites, list)
        assert len(sprites) > 0
        assert 'Cat' in sprites
    
    def test_get_sprite_data(self):
        """Test getting sprite data."""
        from scratch import get_sprite_data
        
        cat = get_sprite_data('Cat')
        assert cat is not None
        assert 'costumes' in cat
        assert 'sounds' in cat
        assert len(cat['costumes']) > 0
    
    def test_find_sprite_fuzzy(self):
        """Test fuzzy sprite name matching."""
        from scratch import find_sprite_by_name
        
        # Exact match
        assert find_sprite_by_name('Cat') == 'Cat'
        
        # Case insensitive
        assert find_sprite_by_name('cat') == 'Cat'
        assert find_sprite_by_name('CAT') == 'Cat'


class TestCLI:
    """Tests for the command-line interface."""
    
    def test_cli_import(self):
        """Test that CLI can be imported."""
        from scratch.cli import main
        assert main is not None


class TestSaveLoad:
    """Tests for saving and loading .sb3 files."""
    
    def test_save_sb3(self):
        """Test saving a project to .sb3 file."""
        from scratch import transpile_to_json, save_sb3
        import zipfile
        
        code = '''
class Cat:
    def when_flag_clicked(self):
        say("Hello!")
'''
        json_str = transpile_to_json(code)
        
        with tempfile.NamedTemporaryFile(suffix='.sb3', delete=False) as f:
            temp_path = f.name
        
        try:
            save_sb3(json_str, temp_path)
            
            # Verify it's a valid zip
            assert zipfile.is_zipfile(temp_path)
            
            # Verify it contains project.json
            with zipfile.ZipFile(temp_path, 'r') as zf:
                assert 'project.json' in zf.namelist()
                
                # Verify project.json is valid
                project = json.loads(zf.read('project.json'))
                assert 'targets' in project
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
