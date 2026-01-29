"""
Asset handling for custom sprites, costumes, backdrops, and sounds.

This module provides utilities for loading and processing custom assets
from files (PNG, SVG, WAV, MP3) for use in Scratch projects.
"""

import os
import hashlib
import base64
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List


def get_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file."""
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def get_data_hash(data: bytes) -> str:
    """Calculate MD5 hash of bytes data."""
    return hashlib.md5(data).hexdigest()


def get_string_hash(content: str) -> str:
    """Calculate MD5 hash of a string."""
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def get_image_dimensions(file_path: str) -> Tuple[int, int]:
    """
    Get dimensions of an image file.
    Returns (width, height).
    
    Supports PNG, SVG (parsed from viewBox or width/height attributes).
    """
    ext = Path(file_path).suffix.lower()
    
    if ext == '.png':
        # Read PNG header to get dimensions
        with open(file_path, 'rb') as f:
            data = f.read(24)
            if data[:8] == b'\x89PNG\r\n\x1a\n':
                # PNG signature found
                width = int.from_bytes(data[16:20], 'big')
                height = int.from_bytes(data[20:24], 'big')
                return (width, height)
    
    elif ext == '.svg':
        # Parse SVG for dimensions
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return get_svg_dimensions(content)
    
    # Default fallback
    return (100, 100)


def get_svg_dimensions(svg_content: str) -> Tuple[int, int]:
    """Extract dimensions from SVG content."""
    import re
    
    # Try viewBox first
    viewbox_match = re.search(r'viewBox\s*=\s*["\']([^"\']+)["\']', svg_content)
    if viewbox_match:
        parts = viewbox_match.group(1).split()
        if len(parts) >= 4:
            try:
                width = float(parts[2])
                height = float(parts[3])
                return (int(width), int(height))
            except ValueError:
                pass
    
    # Try width/height attributes
    width_match = re.search(r'width\s*=\s*["\']?(\d+)', svg_content)
    height_match = re.search(r'height\s*=\s*["\']?(\d+)', svg_content)
    
    width = int(width_match.group(1)) if width_match else 100
    height = int(height_match.group(1)) if height_match else 100
    
    return (width, height)


def load_costume_from_file(
    name: str,
    file_path: str,
    rotation_center_x: int = None,
    rotation_center_y: int = None,
    base_path: str = None
) -> Tuple[Dict[str, Any], bytes]:
    """
    Load a costume from an image file.
    
    Args:
        name: Costume name
        file_path: Path to image file (PNG or SVG)
        rotation_center_x: X center for rotation (default: center of image)
        rotation_center_y: Y center for rotation (default: center of image)
        base_path: Base path for resolving relative file paths
        
    Returns:
        Tuple of (costume_dict, asset_bytes)
    """
    # Resolve path
    if base_path and not os.path.isabs(file_path):
        full_path = os.path.join(base_path, file_path)
    else:
        full_path = file_path
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Costume file not found: {full_path}")
    
    ext = Path(full_path).suffix.lower()
    
    # Read file data
    with open(full_path, 'rb') as f:
        data = f.read()
    
    # Calculate hash
    asset_id = get_data_hash(data)
    
    # Determine format
    if ext == '.png':
        data_format = 'png'
        bitmap_resolution = 2  # PNG is typically higher resolution
    elif ext in ('.svg', '.xml'):
        data_format = 'svg'
        bitmap_resolution = 1
    else:
        raise ValueError(f"Unsupported costume format: {ext}")
    
    # Get dimensions for rotation center
    width, height = get_image_dimensions(full_path)
    
    if rotation_center_x is None:
        rotation_center_x = width // 2
    if rotation_center_y is None:
        rotation_center_y = height // 2
    
    costume_dict = {
        "name": name,
        "bitmapResolution": bitmap_resolution,
        "dataFormat": data_format,
        "assetId": asset_id,
        "md5ext": f"{asset_id}.{data_format}",
        "rotationCenterX": rotation_center_x,
        "rotationCenterY": rotation_center_y
    }
    
    return costume_dict, data


def load_costume_from_svg(
    name: str,
    svg_content: str,
    rotation_center_x: int = None,
    rotation_center_y: int = None
) -> Tuple[Dict[str, Any], bytes]:
    """
    Load a costume from SVG string content.
    
    Args:
        name: Costume name
        svg_content: SVG content as string
        rotation_center_x: X center for rotation
        rotation_center_y: Y center for rotation
        
    Returns:
        Tuple of (costume_dict, asset_bytes)
    """
    data = svg_content.encode('utf-8')
    asset_id = get_data_hash(data)
    
    # Get dimensions
    width, height = get_svg_dimensions(svg_content)
    
    if rotation_center_x is None:
        rotation_center_x = width // 2
    if rotation_center_y is None:
        rotation_center_y = height // 2
    
    costume_dict = {
        "name": name,
        "bitmapResolution": 1,
        "dataFormat": "svg",
        "assetId": asset_id,
        "md5ext": f"{asset_id}.svg",
        "rotationCenterX": rotation_center_x,
        "rotationCenterY": rotation_center_y
    }
    
    return costume_dict, data


def load_backdrop_from_file(
    name: str,
    file_path: str,
    base_path: str = None
) -> Tuple[Dict[str, Any], bytes]:
    """
    Load a backdrop from an image file.
    
    Args:
        name: Backdrop name
        file_path: Path to image file (PNG or SVG)
        base_path: Base path for resolving relative file paths
        
    Returns:
        Tuple of (backdrop_dict, asset_bytes)
    """
    # Resolve path
    if base_path and not os.path.isabs(file_path):
        full_path = os.path.join(base_path, file_path)
    else:
        full_path = file_path
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Backdrop file not found: {full_path}")
    
    ext = Path(full_path).suffix.lower()
    
    # Read file data
    with open(full_path, 'rb') as f:
        data = f.read()
    
    # Calculate hash
    asset_id = get_data_hash(data)
    
    # Determine format
    if ext == '.png':
        data_format = 'png'
        bitmap_resolution = 2
    elif ext in ('.svg', '.xml'):
        data_format = 'svg'
        bitmap_resolution = 1
    else:
        raise ValueError(f"Unsupported backdrop format: {ext}")
    
    backdrop_dict = {
        "name": name,
        "bitmapResolution": bitmap_resolution,
        "dataFormat": data_format,
        "assetId": asset_id,
        "md5ext": f"{asset_id}.{data_format}",
        "rotationCenterX": 240,  # Standard Scratch stage center
        "rotationCenterY": 180
    }
    
    return backdrop_dict, data


def load_backdrop_from_svg(
    name: str,
    svg_content: str
) -> Tuple[Dict[str, Any], bytes]:
    """
    Load a backdrop from SVG string content.
    """
    data = svg_content.encode('utf-8')
    asset_id = get_data_hash(data)
    
    backdrop_dict = {
        "name": name,
        "bitmapResolution": 1,
        "dataFormat": "svg",
        "assetId": asset_id,
        "md5ext": f"{asset_id}.svg",
        "rotationCenterX": 240,
        "rotationCenterY": 180
    }
    
    return backdrop_dict, data


def load_sound_from_file(
    name: str,
    file_path: str,
    base_path: str = None
) -> Tuple[Dict[str, Any], bytes]:
    """
    Load a sound from an audio file.
    
    Args:
        name: Sound name
        file_path: Path to audio file (WAV or MP3)
        base_path: Base path for resolving relative file paths
        
    Returns:
        Tuple of (sound_dict, asset_bytes)
    """
    # Resolve path
    if base_path and not os.path.isabs(file_path):
        full_path = os.path.join(base_path, file_path)
    else:
        full_path = file_path
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Sound file not found: {full_path}")
    
    ext = Path(full_path).suffix.lower()
    
    # Read file data
    with open(full_path, 'rb') as f:
        data = f.read()
    
    # Calculate hash
    asset_id = get_data_hash(data)
    
    # Determine format and get audio info
    if ext == '.wav':
        data_format = 'wav'
        rate, sample_count = get_wav_info(data)
    elif ext == '.mp3':
        data_format = 'mp3'
        # MP3 doesn't need rate/sampleCount for Scratch
        rate = 48000  # Default
        sample_count = len(data)  # Approximation
    else:
        raise ValueError(f"Unsupported sound format: {ext}")
    
    sound_dict = {
        "name": name,
        "assetId": asset_id,
        "dataFormat": data_format,
        "format": "",  # Empty for wav/mp3
        "rate": rate,
        "sampleCount": sample_count,
        "md5ext": f"{asset_id}.{data_format}"
    }
    
    return sound_dict, data


def get_wav_info(data: bytes) -> Tuple[int, int]:
    """
    Extract sample rate and sample count from WAV data.
    
    Returns (sample_rate, sample_count)
    """
    try:
        # WAV header parsing
        if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
            return (48000, len(data))
        
        # Find fmt chunk
        pos = 12
        while pos < len(data) - 8:
            chunk_id = data[pos:pos+4]
            chunk_size = int.from_bytes(data[pos+4:pos+8], 'little')
            
            if chunk_id == b'fmt ':
                # Audio format at pos+8 (2 bytes)
                # Num channels at pos+10 (2 bytes)
                # Sample rate at pos+12 (4 bytes)
                sample_rate = int.from_bytes(data[pos+12:pos+16], 'little')
                
                # Continue to find data chunk for sample count
                pos += 8 + chunk_size
                continue
            
            elif chunk_id == b'data':
                # Data size / (channels * bits_per_sample / 8)
                # Simplified: assume stereo 16-bit
                sample_count = chunk_size // 4
                return (sample_rate if 'sample_rate' in dir() else 48000, sample_count)
            
            pos += 8 + chunk_size
        
        return (48000, len(data))
    except Exception:
        return (48000, len(data))


def create_default_costume_svg(
    name: str,
    color: str = "#4C97FF",
    width: int = 100,
    height: int = 100
) -> Tuple[Dict[str, Any], bytes]:
    """
    Create a simple default costume SVG (colored circle).
    
    Used when no custom costume is provided.
    """
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <circle cx="{width//2}" cy="{height//2}" r="{min(width, height)//2 - 5}" 
          fill="{color}" stroke="#3373CC" stroke-width="3"/>
  <text x="{width//2}" y="{height//2 + 5}" text-anchor="middle" 
        font-family="Arial" font-size="14" fill="white">{name[:3]}</text>
</svg>'''
    
    data = svg.encode('utf-8')
    asset_id = get_data_hash(data)
    
    costume_dict = {
        "name": name,
        "bitmapResolution": 1,
        "dataFormat": "svg",
        "assetId": asset_id,
        "md5ext": f"{asset_id}.svg",
        "rotationCenterX": width // 2,
        "rotationCenterY": height // 2
    }
    
    return costume_dict, data


class AssetManager:
    """
    Manages custom assets for a Scratch project.
    
    Collects costumes, sounds, and backdrops from various sources
    and prepares them for inclusion in the .sb3 file.
    """
    
    def __init__(self, base_path: str = None):
        """
        Initialize asset manager.
        
        Args:
            base_path: Base path for resolving relative file paths
        """
        self.base_path = base_path or os.getcwd()
        # Maps md5ext -> bytes
        self.assets: Dict[str, bytes] = {}
    
    def add_costume(
        self,
        name: str,
        file_path: str = None,
        svg_string: str = None,
        rotation_center_x: int = None,
        rotation_center_y: int = None
    ) -> Dict[str, Any]:
        """
        Add a costume and return its dictionary.
        """
        if svg_string:
            costume_dict, data = load_costume_from_svg(
                name, svg_string, rotation_center_x, rotation_center_y
            )
        elif file_path:
            costume_dict, data = load_costume_from_file(
                name, file_path, rotation_center_x, rotation_center_y, self.base_path
            )
        else:
            # Create default costume
            costume_dict, data = create_default_costume_svg(name)
        
        self.assets[costume_dict['md5ext']] = data
        return costume_dict
    
    def add_backdrop(
        self,
        name: str,
        file_path: str = None,
        svg_string: str = None
    ) -> Dict[str, Any]:
        """
        Add a backdrop and return its dictionary.
        """
        if svg_string:
            backdrop_dict, data = load_backdrop_from_svg(name, svg_string)
        elif file_path:
            backdrop_dict, data = load_backdrop_from_file(name, file_path, self.base_path)
        else:
            raise ValueError("Must provide file_path or svg_string for backdrop")
        
        self.assets[backdrop_dict['md5ext']] = data
        return backdrop_dict
    
    def add_sound(
        self,
        name: str,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Add a sound and return its dictionary.
        """
        sound_dict, data = load_sound_from_file(name, file_path, self.base_path)
        self.assets[sound_dict['md5ext']] = data
        return sound_dict
    
    def get_assets(self) -> Dict[str, bytes]:
        """Get all collected assets."""
        return self.assets
