"""
Command-line interface for the Scratch Transpiler.

Usage:
    scratch py2sb3 input.py output.sb3     # Python to Scratch
    scratch sb32py input.sb3 output.py     # Scratch to Python  
    scratch roundtrip input.sb3 output.sb3 # Round-trip conversion
"""

import argparse
import sys
from pathlib import Path


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
    
    # Import here to avoid slow startup
    from . import transpile_to_json, save_sb3, convert_sb3_to_py, roundtrip_sb3
    
    try:
        if args.command == 'py2sb3':
            input_path = Path(args.input)
            output_path = args.output or str(input_path.with_suffix('.sb3'))
            
            print(f"Converting: {input_path} -> {output_path}")
            
            with open(input_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            json_str = transpile_to_json(code)
            save_sb3(json_str, output_path)
            
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
