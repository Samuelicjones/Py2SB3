"""
Scratch Sprite & Sound Library - Downloads and caches official Scratch assets

This module provides access to all 339 official Scratch sprites and sounds.
Sprite definitions are loaded from scratch_sprites_library.json (fetched from scratch-gui).
Assets are downloaded from the Scratch CDN and cached locally.
"""

import os
import json
import urllib.request
import urllib.error
import time
from typing import Dict, List, Optional, Any
from importlib import resources

# Scratch asset CDN URLs (try multiple in case one is down)
SCRATCH_ASSET_URLS = [
    "https://assets.scratch.mit.edu/internalapi/asset/{md5ext}/get/",
    "https://cdn.assets.scratch.mit.edu/internalapi/asset/{md5ext}/get/",
]

# Local cache directory (user's home directory for persistence)
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".scratch_transpiler", "asset_cache")

# ============================================================================
# Load sprite library from bundled JSON
# ============================================================================

def _get_data_path(filename: str) -> str:
    """Get path to bundled data file."""
    try:
        # Python 3.9+
        ref = resources.files('scratch.data').joinpath(filename)
        return str(ref)
    except (AttributeError, TypeError):
        # Fallback for older Python
        package_dir = os.path.dirname(__file__)
        return os.path.join(package_dir, 'data', filename)


def load_sprite_library() -> Dict[str, Any]:
    """Load the sprite library from bundled JSON file."""
    try:
        json_path = _get_data_path('sprites_library.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                sprites_list = json.load(f)
                return {sprite['name']: sprite for sprite in sprites_list}
    except Exception as e:
        pass
    return {}


def load_sounds_library() -> Dict[str, Any]:
    """Load the sounds library from bundled JSON file."""
    try:
        json_path = _get_data_path('sounds_library.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                sounds_list = json.load(f)
                return {sound['name']: sound for sound in sounds_list}
    except Exception as e:
        pass
    return {}


# Load libraries on import
SPRITE_LIBRARY = load_sprite_library()
SOUNDS_LIBRARY = load_sounds_library()

# ============================================================================
# Asset Download Functions
# ============================================================================

def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def get_cache_path(asset_id: str, data_format: str) -> str:
    """Get the cache file path for an asset."""
    return os.path.join(CACHE_DIR, f"{asset_id}.{data_format}")


def download_asset(asset_id: str, data_format: str, max_retries: int = 3, verbose: bool = True) -> Optional[bytes]:
    """
    Download an asset from the Scratch CDN with retry logic.
    Returns the asset data as bytes, or None if download fails.
    """
    md5ext = f"{asset_id}.{data_format}"
    
    for url_template in SCRATCH_ASSET_URLS:
        url = url_template.format(md5ext=md5ext)
        
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://scratch.mit.edu/'
                })
                with urllib.request.urlopen(req, timeout=15) as response:
                    return response.read()
            except urllib.error.HTTPError as e:
                if e.code == 503 and attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    if verbose:
                        print(f"    CDN returned 503, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                elif attempt < max_retries - 1:
                    time.sleep(1)
                    continue
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
    
    return None


def get_cached_asset(asset_id: str, data_format: str, verbose: bool = True) -> Optional[bytes]:
    """
    Get an asset from cache or download it.
    Returns the asset data as bytes.
    """
    ensure_cache_dir()
    cache_path = get_cache_path(asset_id, data_format)
    
    # Check cache first
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            return f.read()
    
    # Download and cache
    if verbose:
        print(f"  Downloading {asset_id}.{data_format}...")
    data = download_asset(asset_id, data_format, verbose=verbose)
    
    if data:
        with open(cache_path, 'wb') as f:
            f.write(data)
        return data
    else:
        if verbose:
            print(f"    Failed to download {asset_id}.{data_format}")
        return None


# ============================================================================
# Sprite Data Functions
# ============================================================================

def get_sprite_names() -> List[str]:
    """Get list of all available sprite names."""
    return sorted(SPRITE_LIBRARY.keys())


def list_sprites() -> List[str]:
    """Alias for get_sprite_names()."""
    return get_sprite_names()


def get_sprite_data(sprite_name: str) -> Optional[Dict]:
    """Get the full sprite data for a sprite name (case-insensitive)."""
    if sprite_name in SPRITE_LIBRARY:
        return SPRITE_LIBRARY[sprite_name]
    
    for name, data in SPRITE_LIBRARY.items():
        if name.lower() == sprite_name.lower():
            return data
    
    return None


def find_sprite_by_name(name: str, fuzzy: bool = True) -> Optional[str]:
    """
    Find a sprite by name, optionally with fuzzy matching.
    Returns the exact sprite name if found.
    """
    if name in SPRITE_LIBRARY:
        return name
    
    if fuzzy:
        name_lower = name.lower()
        for sprite_name in SPRITE_LIBRARY:
            if sprite_name.lower() == name_lower:
                return sprite_name
        
        for sprite_name in SPRITE_LIBRARY:
            if name_lower in sprite_name.lower():
                return sprite_name
    
    return None


def get_costume_data_for_project(sprite_name: str) -> Optional[List[Dict]]:
    """
    Get costume data formatted for use in a Scratch project.
    Downloads assets if not cached.
    Returns list of costume dicts ready for project.json.
    """
    sprite = get_sprite_data(sprite_name)
    if not sprite:
        return None
    
    costumes = []
    for costume in sprite.get('costumes', []):
        asset_id = costume['assetId']
        data_format = costume['dataFormat']
        md5ext = f"{asset_id}.{data_format}"
        
        costume_data = {
            "name": costume['name'],
            "assetId": asset_id,
            "md5ext": md5ext,
            "dataFormat": data_format,
            "rotationCenterX": costume.get('rotationCenterX', 0),
            "rotationCenterY": costume.get('rotationCenterY', 0),
            "bitmapResolution": costume.get('bitmapResolution', 1)
        }
        costumes.append(costume_data)
    
    return costumes


def get_sound_data_for_project(sprite_name: str) -> Optional[List[Dict]]:
    """
    Get sound data for a sprite, formatted for use in a Scratch project.
    Returns list of sound dicts ready for project.json.
    """
    sprite = get_sprite_data(sprite_name)
    if not sprite:
        return None
    
    sounds = []
    for sound in sprite.get('sounds', []):
        asset_id = sound['assetId']
        data_format = sound['dataFormat']
        md5ext = f"{asset_id}.{data_format}"
        
        sound_data = {
            "name": sound['name'],
            "assetId": asset_id,
            "md5ext": md5ext,
            "dataFormat": data_format,
            "format": "",
            "rate": sound.get('rate', 44100),
            "sampleCount": sound.get('sampleCount', 0)
        }
        sounds.append(sound_data)
    
    return sounds


# ============================================================================
# Sound Library Functions (standalone sounds, not sprite sounds)
# ============================================================================

def get_sound_names() -> List[str]:
    """Get list of all available sound names from the sounds library."""
    return sorted(SOUNDS_LIBRARY.keys())


def list_sounds() -> List[str]:
    """Alias for get_sound_names()."""
    return get_sound_names()


def get_library_sound_data(sound_name: str) -> Optional[Dict]:
    """Get the full sound data for a sound name from sounds library (case-insensitive)."""
    if sound_name in SOUNDS_LIBRARY:
        return SOUNDS_LIBRARY[sound_name]
    
    for name, data in SOUNDS_LIBRARY.items():
        if name.lower() == sound_name.lower():
            return data
    
    return None


def find_sound_by_name(name: str, fuzzy: bool = True) -> Optional[str]:
    """
    Find a sound by name, optionally with fuzzy matching.
    Returns the exact sound name if found.
    """
    if name in SOUNDS_LIBRARY:
        return name
    
    if fuzzy:
        name_lower = name.lower()
        for sound_name in SOUNDS_LIBRARY:
            if sound_name.lower() == name_lower:
                return sound_name
        
        for sound_name in SOUNDS_LIBRARY:
            if name_lower in sound_name.lower():
                return sound_name
    
    return None


def get_library_sound_for_project(sound_name: str) -> Optional[Dict]:
    """
    Get sound data from the sounds library formatted for use in a Scratch project.
    Returns a sound dict ready for project.json, or None if not found.
    """
    sound = get_library_sound_data(sound_name)
    if not sound:
        return None
    
    asset_id = sound['assetId']
    data_format = sound.get('dataFormat', '') or 'wav'
    md5ext = sound.get('md5ext', f"{asset_id}.{data_format}")
    
    if not data_format and '.' in md5ext:
        data_format = md5ext.split('.')[-1]
    
    sound_data = {
        "name": sound['name'],
        "assetId": asset_id,
        "md5ext": md5ext,
        "dataFormat": data_format,
        "format": "",
        "rate": sound.get('rate', 44100),
        "sampleCount": sound.get('sampleCount', 0)
    }
    
    return sound_data


def download_library_sound(sound_name: str, verbose: bool = True) -> bool:
    """
    Download a sound from the sounds library to the cache.
    Returns True if successful.
    """
    sound = get_library_sound_data(sound_name)
    if not sound:
        if verbose:
            print(f"Sound '{sound_name}' not found in sounds library")
        return False
    
    asset_id = sound['assetId']
    md5ext = sound.get('md5ext', '')
    
    if '.' in md5ext:
        data_format = md5ext.split('.')[-1]
    else:
        data_format = sound.get('dataFormat', '') or 'wav'
    
    data = get_cached_asset(asset_id, data_format, verbose=verbose)
    return data is not None


def download_sprite_assets(sprite_name: str, verbose: bool = True) -> Dict[str, bool]:
    """
    Download all assets (costumes and sounds) for a sprite.
    Returns dict mapping asset md5ext to success status.
    """
    sprite = get_sprite_data(sprite_name)
    if not sprite:
        if verbose:
            print(f"Sprite '{sprite_name}' not found in library")
        return {}
    
    results = {}
    
    for costume in sprite.get('costumes', []):
        asset_id = costume['assetId']
        data_format = costume['dataFormat']
        md5ext = f"{asset_id}.{data_format}"
        data = get_cached_asset(asset_id, data_format, verbose=verbose)
        results[md5ext] = data is not None
    
    for sound in sprite.get('sounds', []):
        asset_id = sound['assetId']
        data_format = sound['dataFormat']
        md5ext = f"{asset_id}.{data_format}"
        data = get_cached_asset(asset_id, data_format, verbose=verbose)
        results[md5ext] = data is not None
    
    return results
