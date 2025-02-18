import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Optional

@dataclass
class SubtitleSettings:
    font: str = "Arial"
    font_size: str = "48"
    primary_color: str = "&HFFFFFF&"
    outline_color: str = "&H000000&"
    back_color: str = "&H000000&"
    outline: str = "2"
    shadow: str = "0"
    margin_v: str = "20"
    margin_h: str = "20"
    alignment: str = "2"
    max_chars: str = "40"
    name: str = "Default"  # Name of the preset

class SubtitlePresetManager:
    def __init__(self, presets_file: str = "subtitle_presets.json"):
        self.presets_file = presets_file
        self.presets: Dict[str, SubtitleSettings] = {}
        self.load_presets()

    def load_presets(self):
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.presets = {
                        name: SubtitleSettings(**settings)
                        for name, settings in data.items()
                    }
            except Exception as e:
                print(f"Error loading presets: {e}")
                # Initialize with default preset if loading fails
                self.presets = {"Default": SubtitleSettings()}
        else:
            # Create default preset if file doesn't exist
            self.presets = {"Default": SubtitleSettings()}
            self.save_presets()

    def save_presets(self):
        try:
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump({
                    name: asdict(settings)
                    for name, settings in self.presets.items()
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving presets: {e}")

    def add_preset(self, settings: SubtitleSettings):
        self.presets[settings.name] = settings
        self.save_presets()

    def get_preset(self, name: str) -> Optional[SubtitleSettings]:
        return self.presets.get(name)

    def delete_preset(self, name: str):
        if name in self.presets and name != "Default":
            del self.presets[name]
            self.save_presets()

    def get_preset_names(self):
        return list(self.presets.keys())
