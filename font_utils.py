from tkinter import font
from typing import List

def get_system_fonts() -> List[str]:
    """Get list of installed system fonts"""
    # Get all system fonts
    font_names = list(font.families())
    
    # Remove duplicates and sort
    font_names = sorted(list(set(font_names)))
    
    # Filter out special fonts and ensure proper font names
    filtered_fonts = []
    for name in font_names:
        # Skip fonts starting with @ (vertical fonts in Windows)
        if name.startswith('@'):
            continue
        # Skip empty or special characters
        if not name or name.startswith('.'):
            continue
        filtered_fonts.append(name)
    
    return filtered_fonts
